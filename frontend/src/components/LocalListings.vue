<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { recordDetailView } from '../utils/interactions.js'

const props = defineProps({
    attractions: { type: Array, default: () => [] },
    account: { type: Object, default: null },
    accountReady: { type: Promise, default: null }
})

// 页面数据
const items = ref([])
const loading = ref(false)
const error = ref('')

// 页面状态
const kind = ref('food')
const keyword = ref('')
const area = ref('')
const label = ref('')
const foodGroup = ref('')
const sort = ref('distance')
const referenceId = ref('')
const selectedItem = ref(null)
let reviewController = null
const detailsVisible = computed({
    get() {
        return selectedItem.value !== null
    },

    set(visible) {
        if (!visible && !reviewSubmitting.value) {
            reviewController?.abort()
            selectedItem.value = null
            reviewLoading.value = false
        }
    }
})

// 收藏操作状态
const bookmarkLoadingId = ref(null)
const actionError = ref('')

// 评价数据
const reviews = ref([])
const myReview = ref(null)
const reviewLoggedIn = ref(false)
const reviewRating = ref(5)
const reviewBody = ref('')
const reviewLoading = ref(false)
const reviewSubmitting = ref(false)
const reviewError = ref('')
const reviewMessage = ref('')

// 获取美食和文创  GET
async function loadListings() {
    loading.value = true
    error.value = ''

    try {
        const response = await fetch('/api/listings/', {
            method: 'GET'
        })

        if (!response.ok) { throw new Error(`HTTP ${response.status}`) }
        const data = await response.json()
        items.value = data.items || []
    } catch (err) {
        error.value = err.message || '获取数据失败'
    } finally {
        loading.value = false
    }
}

// Only this user-triggered entry records a detail view.
function openDetails(item) {
    void recordDetailView({
        account: props.account ?? props.accountReady,
        targetType: 'listing',
        targetId: item.id
    })
    return refreshDetails(item)
}

// 加载评价；提交评价后的自动刷新不新增浏览记录。
async function refreshDetails(item) {
    // 取消上次加载，旧响应和 finally 都不能覆盖新商户的评价状态。
    reviewController?.abort()
    const controller = new AbortController()
    reviewController = controller
    selectedItem.value = item
    reviews.value = []
    myReview.value = null
    reviewLoggedIn.value = false
    reviewRating.value = 5
    reviewBody.value = ''
    reviewError.value = ''
    reviewMessage.value = ''
    reviewLoading.value = true

    try {
        const response = await fetch(`/api/listings/${item.id}/reviews/`, {
            signal: controller.signal
        })

        if (!response.ok) { throw new Error(`HTTP ${response.status}`) }
        const data = await response.json()

        if (controller.signal.aborted) return
        reviews.value = data.items
        myReview.value = data.my_review
        reviewLoggedIn.value = data.authenticated

        reviewRating.value = myReview.value?.rating || 5
        reviewBody.value = myReview.value?.body || ''
    } catch (err) {
        if (!controller.signal.aborted) reviewError.value = err.message
    } finally {
        if (!controller.signal.aborted) reviewLoading.value = false
    }
}

// 提交评价  POST
async function submitReview() {
    if (
        !selectedItem.value ||
        reviewSubmitting.value ||
        reviewLoading.value
    ) return

    if (!reviewBody.value.trim()) {
        reviewError.value = '请输入评价内容'
        return
    }

    reviewSubmitting.value = true
    reviewError.value = ''
    reviewMessage.value = ''

    const item = selectedItem.value
    const form = new FormData()

    form.set('rating', reviewRating.value)
    form.set('body', reviewBody.value)

    try {
        const response = await fetch(`/api/listings/${item.id}/reviews/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken() }, body: form
        })

        const data = await response.json()
        if (!response.ok) { throw new Error(data.error || '提交失败') }

        await refreshDetails(item)
        reviewMessage.value = data.message
        await loadListings()
    } catch (err) {
        reviewError.value = err.message
    } finally {
        reviewSubmitting.value = false
    }
}

// 获取 CSRF Token
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
    return cookie ? cookie.split('=')[1] : ''
}

// 收藏或取消收藏   DELETE POST
async function toggleBookmark(item) {
    // 如果没有登录，跳转到登录页面
    if (!props.account?.authenticated) {
        window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.href)}`
        return
    }

    if (bookmarkLoadingId.value !== null) return
    bookmarkLoadingId.value = item.id
    actionError.value = ''

    try {
        const response = await fetch(
            `/api/listings/${item.id}/bookmark/`,
            {
                method: item.bookmarked ? 'DELETE' : 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() }
            }
        )

        if (response.status === 401) {
            window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.href)}`
            return
        }
        if (!response.ok) { throw new Error(`HTTP ${response.status}`) }

        const data = await response.json()

        items.value = items.value.map(listing =>
            listing.id === item.id ? { ...listing, bookmarked: data.bookmarked } : listing
        )

    } catch (err) {
        actionError.value = err.message || '收藏操作失败'
    } finally {
        bookmarkLoadingId.value = null
    }
}

// 根据当前分类筛选
const currentItems = computed(() => {
    return items.value.filter(item => item.kind === kind.value)
})

// 区域选项
const areas = computed(() => { return [...new Map(currentItems.value.map(item => [item.area, item.area_label]))] })

// 菜品与店型选项
const labels = computed(() => { return [...new Set(currentItems.value.map(item => item.label).filter(Boolean))] })

// 美食主题
const foodGroups = computed(() => {
    return [...new Map(
        currentItems.value
            .filter(item => item.food_group)
            .map(item => [item.food_group, item.food_group_label])
    )]
})

// 获取参考景点
const referencePlace = computed(() => {
    // props 是 Vue 父组件向子组件传递的数据
    return props.attractions.find(item => item.id === Number(referenceId.value)
    ) || props.attractions.find(
        item => item.name === '议事亭前地'
    ) || props.attractions[0] || null
})

// 计算两点之间的直线距离
function calculateDistance(place, item) {
    if (!place || item.lat == null || item.lng == null) { return null }

    const rad = Math.PI / 180
    const lat1 = Number(place.lat)
    const lng1 = Number(place.lng)
    const lat2 = Number(item.lat)
    const lng2 = Number(item.lng)

    const a =
        Math.sin((lat2 - lat1) * rad / 2) ** 2 +
        Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin((lng2 - lng1) * rad / 2) ** 2

    return 6371 * 2 * Math.asin(Math.sqrt(Math.min(a, 1)))
}

// 距离显示
function distanceText(km) {
    if (km < 1) {
        return `${Math.round(km * 1000)} 米`
    }
    return `${km.toFixed(1)} 公里`
}

// 搜索、筛选、排序
const visibleItems = computed(() => {
    const q = keyword.value.trim().toLowerCase()

    const results = currentItems.value
        .filter(item => {
            const matchesKeyword = !q || [
                item.name, item.label, item.address, item.summary, item.food_group_label
            ].filter(Boolean).some(value => String(value).toLowerCase().includes(q))    // some() 判断是否至少有一个字段匹配

            const matchesArea = !area.value || item.area === area.value
            const matchesLabel = !label.value || item.label === label.value
            const matchesGroup = !foodGroup.value || item.food_group === foodGroup.value

            return matchesKeyword && matchesArea && matchesLabel && matchesGroup
        }).map(item => ({
            ...item, distance: kind.value === 'food'
                ? calculateDistance(referencePlace.value, item)
                : null
        }))

    if (sort.value === 'distance') {
        results.sort((a, b) => (a.distance ?? Infinity) - (b.distance ?? Infinity))  // 空值的时候用 ?? 右边的值
    } else { results.sort((a, b) => (b.rating ?? -1) - (a.rating ?? -1) || b.review_count - a.review_count) }
    return results
})

// 切换分类时重置筛选
watch(kind, () => {
    keyword.value = ''
    area.value = ''
    label.value = ''
    foodGroup.value = ''
    sort.value = kind.value === 'food' ? 'distance' : 'rating'
    detailsVisible.value = false
})

// 清空筛选  全部改为 ""
function resetFilters() {
    keyword.value = ''
    area.value = ''
    label.value = ''
    foodGroup.value = ''
}

// 页面初始化
onMounted(loadListings)
onUnmounted(() => reviewController?.abort())
</script>

<template>
    <section>
        <div class="section-heading">
            <div>
                <p class="eyebrow">MACAO DISCOVERY</p>
                <h2>{{ kind === 'food' ? '澳门地道美食' : '文创与手信' }}</h2>
                <p>{{ kind === 'food' ? '从街坊小吃到葡国料理，探索澳门的味道。' : '发现澳门文化与历史建筑衍生的特色文创。' }}</p>
            </div>
            <el-radio-group v-model="kind" aria-label="内容分类">
                <el-radio-button value="food">地道美食</el-radio-button>
                <el-radio-button value="product">文创手信</el-radio-button>
            </el-radio-group>
        </div>

        <el-card shadow="never">
            <el-form label-position="top" @submit.prevent>
                <el-row :gutter="16">
                    <el-col :xs="24" :sm="12" :lg="8">
                        <el-form-item label="搜索商户">
                            <el-input v-model="keyword" placeholder="搜索名称、类型或地址..." clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :xs="24" :sm="12" :lg="8">
                        <el-form-item label="区域">
                            <el-select v-model="area" :empty-values="[null, undefined]">
                                <el-option label="全部区域" value="" />
                                <el-option v-for="[id, name] in areas" :key="id" :label="name" :value="id" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :xs="24" :sm="12" :lg="8">
                        <el-form-item label="类别">
                            <el-select v-model="label" :empty-values="[null, undefined]">
                                <el-option label="全部类别" value="" />
                                <el-option v-for="item in labels" :key="item" :label="item" :value="item" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col v-if="kind === 'food'" :xs="24" :sm="12" :lg="8">
                        <el-form-item label="美食主题">
                            <el-select v-model="foodGroup" :empty-values="[null, undefined]">
                                <el-option label="全部美食主题" value="" />
                                <el-option v-for="[id, name] in foodGroups" :key="id" :label="name" :value="id" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :xs="24" :sm="12" :lg="8">
                        <el-form-item label="排序方式">
                            <el-select v-model="sort">
                                <el-option v-if="kind === 'food'" label="距离优先" value="distance" />
                                <el-option label="评分优先" value="rating" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col v-if="kind === 'food' && attractions.length" :xs="24" :sm="12" :lg="8">
                        <el-form-item label="距离参考景点">
                            <el-select v-model="referenceId" :empty-values="[null, undefined]" filterable>
                                <el-option label="默认参考景点" value="" />
                                <el-option v-for="place in attractions" :key="place.id" :label="place.name" :value="String(place.id)" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                </el-row>
                <el-button @click="resetFilters">重置筛选</el-button>
            </el-form>
        </el-card>
        <p><el-text type="info">找到 {{ visibleItems.length }} 项内容</el-text></p>
        <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon>
            <el-button @click="loadListings">重试</el-button>
        </el-alert>
        <el-alert v-if="actionError" :title="actionError" type="error" :closable="false" show-icon />
        <div v-loading="loading" element-loading-text="正在加载..." class="loading-region">
            <template v-if="!error">
                <el-row :gutter="20" class="card-row">
                    <el-col v-for="item in visibleItems" :key="item.id" :xs="24" :sm="12" :lg="8">
                        <el-card shadow="hover" class="content-card">
                            <el-image :src="item.image_url || ''" :alt="item.name" fit="cover" loading="lazy" class="card-image">
                                <template #error><div class="image-placeholder">澳门漫遊</div></template>
                            </el-image>
                            <el-space wrap>
                                <el-tag type="info">{{ item.area_label }}</el-tag>
                                <el-tag>{{ item.food_group_label || item.label }}</el-tag>
                            </el-space>
                            <h3>{{ item.name }}</h3>
                            <p class="summary">{{ item.summary }}</p>
                            <el-space wrap>
                                <el-text type="warning">{{ item.rating != null ? `★ ${Number(item.rating).toFixed(1)}` : '暂无评价' }}</el-text>
                                <el-text v-if="item.distance != null" type="info">{{ distanceText(item.distance) }}</el-text>
                                <el-text v-if="item.price" type="info">{{ item.price }}</el-text>
                            </el-space>
                            <el-space wrap class="section-gap">
                                <el-button :type="item.bookmarked ? 'success' : 'default'" :loading="bookmarkLoadingId === item.id"
                                    :disabled="bookmarkLoadingId !== null" @click="toggleBookmark(item)">
                                    {{ item.bookmarked ? '已收藏' : '收藏' }}
                                </el-button>
                                <el-button type="primary" @click="openDetails(item)">查看详情</el-button>
                            </el-space>
                        </el-card>
                    </el-col>
                </el-row>
                <el-empty v-if="!loading && !visibleItems.length" description="没有找到符合条件的内容。" />
            </template>
        </div>

        <el-dialog v-model="detailsVisible" :title="selectedItem?.name || '详情'" width="min(650px, 92vw)"
            :close-on-click-modal="!reviewSubmitting" :close-on-press-escape="!reviewSubmitting" :show-close="!reviewSubmitting">
            <template v-if="selectedItem">
                <el-image v-if="selectedItem.image_url" :src="selectedItem.image_url" :alt="selectedItem.name" fit="cover" class="detail-image" />
                <p><el-text type="info">{{ selectedItem.area_label }}</el-text></p>
                <p>{{ selectedItem.summary }}</p>
                <el-space wrap>
                    <el-tag v-for="tag in selectedItem.tag_labels" :key="tag">{{ tag }}</el-tag>
                </el-space>
                <el-descriptions :column="1" class="section-gap">
                    <el-descriptions-item v-if="selectedItem.address" label="地址">{{ selectedItem.address }}</el-descriptions-item>
                    <el-descriptions-item v-if="selectedItem.price" label="参考价格">{{ selectedItem.price }}</el-descriptions-item>
                </el-descriptions>
                <p v-if="selectedItem.image_credit" class="muted">
                    图片来源：
                    <el-link :href="selectedItem.image_credit.source_url" target="_blank" rel="noopener noreferrer">{{ selectedItem.image_credit.author }}</el-link>
                    · <el-link :href="selectedItem.image_credit.license_url" target="_blank" rel="noopener noreferrer">{{ selectedItem.image_credit.license }}</el-link>
                </p>
                <el-space wrap>
                    <el-link v-if="selectedItem.source_url" :href="selectedItem.source_url" target="_blank" rel="noopener noreferrer">查看资料来源 ↗</el-link>
                    <el-link v-if="selectedItem.navigation_url" :href="selectedItem.navigation_url" target="_blank" rel="noopener noreferrer">Google Maps 导航 ↗</el-link>
                </el-space>
                <el-divider />
                <section v-loading="reviewLoading" element-loading-text="正在加载评价..." class="loading-region">
                    <h3>用户评价</h3>
                    <el-alert v-if="reviewError" :title="reviewError" type="error" :closable="false" show-icon />
                    <el-alert v-if="reviewMessage" :title="reviewMessage" type="success" :closable="false" show-icon />
                    <el-form v-if="reviewLoggedIn" label-position="top" :disabled="reviewSubmitting || reviewLoading" @submit.prevent="submitReview">
                        <p v-if="myReview">我的评价：
                            <el-tag :type="myReview.status === 'approved' ? 'success' : myReview.status === 'pending' ? 'warning' : 'danger'">
                                {{ myReview.status === 'pending' ? '待审核' : myReview.status === 'approved' ? '已通过' : '已拒绝' }}
                            </el-tag>
                        </p>
                        <el-form-item label="评分"><el-rate v-model="reviewRating" show-score score-template="{value}/5" /></el-form-item>
                        <el-form-item label="评价内容">
                            <el-input v-model="reviewBody" type="textarea" :rows="4" maxlength="500" show-word-limit placeholder="分享你的体验..." />
                        </el-form-item>
                        <el-button type="primary" native-type="submit" :loading="reviewSubmitting" :disabled="!reviewBody.trim() || reviewLoading">提交评价</el-button>
                    </el-form>
                    <el-link v-else-if="!reviewLoading" href="/accounts/login/?next=/">登录后发表评价</el-link>
                    <h3>其他游客的评价</h3>
                    <div v-for="review in reviews" :key="review.id">
                        <el-divider />
                        <el-space wrap><strong>{{ review.author }}</strong><el-rate :model-value="review.rating" disabled /></el-space>
                        <p>{{ review.body }}</p>
                    </div>
                    <el-empty v-if="!reviewLoading && !reviews.length" description="暂无公开评价" :image-size="60" />
                </section>
            </template>
        </el-dialog>
    </section>
</template>
