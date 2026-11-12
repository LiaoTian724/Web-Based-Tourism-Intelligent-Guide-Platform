<script setup>
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps({
    attractions: {
        type: Array, default: () => []
    }
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

// 用户登录状态
const account = ref({ authenticated: false })

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



// 获取美食和文创
async function loadListings() {
    loading.value = true
    error.value = ''

    try {
        const response = await fetch('/api/listings/')

        if (!response.ok) {throw new Error(`HTTP ${response.status}`)}

        const data = await response.json()
        items.value = data.items || []

    } catch (err) {
        error.value = err.message || '获取数据失败'
    } finally {
        loading.value = false
    }
}



// 加载评价
async function openDetails(item) {

    selectedItem.value = item
    reviews.value = []
    myReview.value = null

    reviewError.value = ''
    reviewMessage.value = ''
    reviewLoading.value = true

    try {
        const response = await fetch(
            `/api/listings/${item.id}/reviews/`
        )

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()

        reviews.value = data.items
        myReview.value = data.my_review
        reviewLoggedIn.value = data.authenticated

        reviewRating.value = myReview.value?.rating || 5
        reviewBody.value = myReview.value?.body || ''

    } catch (err) {
        reviewError.value = err.message
    } finally {
        reviewLoading.value = false
    }
}



// 提交评价
async function submitReview() {
    if (!selectedItem.value || reviewSubmitting.value) return

    reviewSubmitting.value = true
    reviewError.value = ''
    reviewMessage.value = ''

    const form = new FormData()

    form.set('rating', reviewRating.value)
    form.set('body', reviewBody.value)

    try {
        const response = await fetch(`/api/listings/${selectedItem.value.id}/reviews/`,
            {method: 'POST', headers: {'X-CSRFToken': getCsrfToken()}, body: form}
        )

        const data = await response.json()

        if (!response.ok) {throw new Error(data.error || '提交失败')}

        const item = selectedItem.value
        await openDetails(item)

        reviewMessage.value = data.message

        await loadListings()

    } catch (err) {
        reviewError.value = err.message
    } finally {
        reviewSubmitting.value = false
    }
}




// 获取用户登录状态
async function loadAccount() {
    try {
        const response = await fetch('/api/account/')

        if (response.ok) {
            account.value = await response.json()
        }
    } catch (err) {
        console.error(err)
    }
}


// 获取 CSRF Token
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
    // 原来的字符串：sessionid=abc123; csrftoken=xyz789; theme=dark 变成
    // [
    //     'sessionid=abc123',
    //     'csrftoken=xyz789',
    //     'theme=dark'
    // ]
    return cookie ? cookie.split('=')[1] : ''
}


// 收藏或取消收藏
async function toggleBookmark(item) {

    // 如果没有登录，跳转到登录页面
    if (!account.value.authenticated) {
        window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.href)}`
        return
    }

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

        // 更新收藏状态
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
const areas = computed(() => {
    return [...new Map(
        currentItems.value.map(item => [item.area, item.area_label])
    )]
})

// 菜品与店型选项
const labels = computed(() => {
    return [...new Set(currentItems.value.map(item => item.label).filter(Boolean))]
})

// 美食主题
const foodGroups = computed(() => {
    return [...new Map(
        currentItems.value
            .filter(item => item.food_group)
            .map(item => [item.food_group, item.food_group_label])
    )]
})

// 当前距离参考点
const referencePlace = computed(() => {
    return props.attractions.find(
        item => item.id === Number(referenceId.value)
    ) || props.attractions.find(
        item => item.name === '议事亭前地'
    ) || props.attractions[0] || null
})

// 计算两点之间的直线距离
function calculateDistance(place, item) {
    if (!place || item.lat == null || item.lng == null) {
        return null
    }

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
                item.name,
                item.label,
                item.address,
                item.summary,
                item.food_group_label
            ].filter(Boolean).some(value =>
                String(value).toLowerCase().includes(q)
            )

            const matchesArea = !area.value || item.area === area.value
            const matchesLabel = !label.value || item.label === label.value
            const matchesGroup = !foodGroup.value || item.food_group === foodGroup.value

            return matchesKeyword && matchesArea && matchesLabel && matchesGroup
        }).map(item => ({ ...item, distance: kind.value === 'food' ? calculateDistance(referencePlace.value, item) : null }))

    if (sort.value === 'distance') {
        results.sort((a, b) => (a.distance ?? Infinity) - (b.distance ?? Infinity))
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
    selectedItem.value = null
})


// 清空筛选
function resetFilters() {
    keyword.value = ''
    area.value = ''
    label.value = ''
    foodGroup.value = ''
}



// 页面初始化
onMounted(async () => {
    await loadAccount()
    await loadListings()
})
</script>

<template>
    <section class="discovery-page">

        <!-- 页面标题 -->
        <div class="discovery-heading">
            <div>
                <p class="discovery-eyebrow">MACAO DISCOVERY</p>
                <h2>{{ kind === 'food' ? '澳门地道美食' : '文创与手信' }}</h2>

                <p>
                    {{ kind === 'food' ? '从街坊小吃到葡国料理，探索澳门的味道。' : '发现澳门文化与历史建筑衍生的特色文创。' }}
                </p>
            </div>

            <div class="discovery-tabs">
                <button :class="{ active: kind === 'food' }" @click="kind = 'food'">地道美食</button>
                <button :class="{ active: kind === 'product' }" @click="kind = 'product'">文创手信</button>
            </div>
        </div>

        <!-- 筛选区域 -->
        <div class="discovery-filter">
            <input v-model="keyword" type="search" placeholder="搜索名称、类型或地址...">
            <select v-model="area">
                <option value="">全部区域</option>
                <option v-for="[id, name] in areas" :key="id" :value="id">{{ name }}</option>
            </select>

            <select v-model="label">
                <option value="">全部类别</option>
                <option v-for="item in labels" :key="item" :value="item">{{ item }}</option>
            </select>

            <select v-if="kind === 'food'" v-model="foodGroup">
                <option value="">全部美食主题</option>
                <option v-for="[id, name] in foodGroups" :key="id" :value="id">{{ name }}</option>
            </select>

            <select v-model="sort">
                <option value="distance" v-if="kind === 'food'">距离优先</option>
                <option value="rating">评分优先</option>
            </select>

            <select v-if="kind === 'food' && attractions.length" v-model="referenceId">
                <option v-for="place in attractions" :key="place.id" :value="String(place.id)">{{ place.name }}</option>
            </select>

            <button class="discovery-reset" @click="resetFilters">重置筛选</button>
        </div>

        <!-- 数据状态 -->
        <p v-if="loading" class="discovery-message">正在加载...</p>

        <p v-else-if="error" class="discovery-message error">{{ error }}<button @click="loadListings">重试</button></p>

        <p v-else class="discovery-count">找到 {{ visibleItems.length }} 项内容</p>
        <p v-if="actionError" class="discovery-message error"> {{ actionError }} </p>

        <!-- 数据卡片 -->
        <div v-if="!loading && !error" class="discovery-grid">
            <article v-for="item in visibleItems" :key="item.id" class="discovery-card">
                <div class="discovery-image">
                    <img v-if="item.image_url" :src="item.image_url" :alt="item.name" loading="lazy">
                    <div v-else class="image-placeholder">澳门漫遊</div>

                    <span class="discovery-area">{{ item.area_label }}</span>
                </div>

                <div class="discovery-card-body">
                    <p class="discovery-label">{{ item.food_group_label || item.label }}</p>

                    <h3>{{ item.name }}</h3>

                    <p class="discovery-summary">{{ item.summary }}</p>

                    <div class="discovery-meta">
                        <span>
                            {{ item.rating != null ? `★ ${Number(item.rating).toFixed(1)}` : '暂无评价' }}
                        </span>

                        <span v-if="item.distance != null">{{ distanceText(item.distance) }}</span>

                        <span v-if="item.price">{{ item.price }}</span>
                    </div>

                    <!-- 收藏按钮 -->
                    <button
                        class="bookmark-button"
                        :class="{ saved: item.bookmarked }"
                        :disabled="bookmarkLoadingId === item.id"
                        @click="toggleBookmark(item)"
                    >
                        {{ bookmarkLoadingId === item.id ? '处理中...' : item.bookmarked ? '已收藏' : '收藏' }}
                    </button>

                    <!-- 查看详情 -->
                    <button class="discovery-detail-button"  @click="openDetails(item)"> 查看详情 </button>
                </div>
            </article>

        </div>

        <div v-if="!loading && !error && !visibleItems.length" class="discovery-message">没有找到符合条件的内容。</div>

        <!-- 详情弹窗 -->
        <div v-if="selectedItem" class="discovery-modal" @click.self="selectedItem = null">
            <div class="discovery-modal-content">

                <button class="discovery-close" @click="selectedItem = null">×</button>

                <img v-if="selectedItem.image_url" :src="selectedItem.image_url" :alt="selectedItem.name">

                <div class="discovery-modal-body">
                    <p class="discovery-label">{{ selectedItem.area_label }}</p>

                    <h2>{{ selectedItem.name }}</h2>
                    <p>{{ selectedItem.summary }}</p>

                    <p v-if="selectedItem.address">地址：{{ selectedItem.address }}</p>
                    <p v-if="selectedItem.price">参考价格：{{ selectedItem.price }}</p>
                    <div v-if="selectedItem.image_credit" class="discovery-credit">
                        图片来源：
                        <a :href="selectedItem.image_credit.source_url" target="_blank" rel="noopener noreferrer">
                            {{ selectedItem.image_credit.author }}
                        </a>

                        ·

                        <a :href="selectedItem.image_credit.license_url" target="_blank" rel="noopener noreferrer">
                            {{ selectedItem.image_credit.license }}
                        </a>
                    </div>

                    <a v-if="selectedItem.source_url" :href="selectedItem.source_url" target="_blank" rel="noopener noreferrer">
                        查看资料来源 ↗
                    </a>

                    <a v-if="selectedItem.navigation_url" :href="selectedItem.navigation_url" target="_blank" rel="noopener noreferrer">
                        Google Maps 导航 ↗
                    </a>


                    <!-- 评价区域 -->
                    <section class="review-section">
                        <h3>用户评价</h3>

                        <p v-if="reviewLoading">正在加载评价...</p>
                        <p v-if="reviewError">{{ reviewError }}</p>
                        <p v-if="reviewMessage">{{ reviewMessage }}</p>

                        <form v-if="reviewLoggedIn" @submit.prevent="submitReview">
                            <p v-if="myReview">我的评价： {{ myReview.status === 'pending' ? '待审核' : myReview.status === 'approved' ? '已通过' : '已拒绝'}}</p>

                            <label>评分
                                <select v-model.number="reviewRating">
                                    <option :value="1">1 星</option>
                                    <option :value="2">2 星</option>
                                    <option :value="3">3 星</option>
                                    <option :value="4">4 星</option>
                                    <option :value="5">5 星</option>
                                </select>
                            </label>

                            <label> 评价内容
                                <textarea v-model="reviewBody" maxlength="500" required placeholder="分享你的体验..."></textarea>
                            </label>

                            <button type="submit" :disabled="reviewSubmitting">{{ reviewSubmitting ? '提交中...' : '提交评价' }}</button>
                        </form>

                        <p v-else><a href="/accounts/login/?next=/">登录后发表评价</a></p>

                        <h3>其他游客的评价</h3>

                        <div v-for="review in reviews" :key="review.id" class="review-item">
                            <strong>{{ review.author }}</strong>
                            <span>★ {{ review.rating }}/5</span>
                            <p>{{ review.body }}</p>
                        </div>

                        <p v-if="!reviewLoading && !reviews.length">暂无公开评价</p>
                    </section>





                </div>
            </div>
        </div>

    </section>
</template>
