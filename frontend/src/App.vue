<script setup>
import { ref, onMounted, computed } from 'vue'
import AttractionMap from './components/AttractionMap.vue'
import LocalListings from './components/LocalListings.vue'
import MyBookmarks from './components/MyBookmarks.vue'
import ItineraryPlanner from './components/ItineraryPlanner.vue'
import { recordDetailView } from './utils/interactions.js'

// 景点数据
// 完整景点目录
const allAttractions = ref([])
// 当前筛选后的景点
const attractions = ref([])
const activePage = ref('attractions')

// 用户信息
const account = ref(null)
const accountReady = ref(null)
const csrfToken = ref('')
const accountError = ref(false)

// 搜索条件
const keyword = ref('')
const region = ref('')
const category = ref('')
const theme = ref('')
const lessKnownOnly = ref(false)

// 最后一次成功查询使用的参数
const appliedQuery = ref(null)

// 页面状态
const loading = ref(false)
const error = ref('')

// 区域选项
const regions = [
    { value: '', label: '全部区域' },
    { value: 'peninsula', label: '澳门半岛' },
    { value: 'taipa', label: '氹仔' },
    { value: 'coloane', label: '路环' }
]

// 分类选项
const categories = [
    { value: '', label: '全部分类' },
    { value: 'history', label: '历史建筑' },
    { value: 'culture', label: '文化地标' },
    { value: 'photography', label: '摄影打卡' },
    { value: 'food', label: '美食体验' }
]
const themes = [
    { value: '', label: '全部主题' },
    { value: 'heritage', label: '澳门世界遗产' },
    { value: 'museums', label: '博物馆及展览厅' },
    { value: 'churches', label: '教堂' },
    { value: 'temples', label: '庙宇' },
    { value: 'parks', label: '公园' },
    { value: 'fortresses', label: '炮台' },
    { value: 'other', label: '其他景点' }
]

// 当前选中的景点
const selectedId = ref(null)
const detailPlace = ref(null)
const detailVisible = ref(false)

// 根据 ID 找到景点
const selectedPlace = computed(() => {
    return attractions.value.find(place => place.id === selectedId.value) || null
})

// 选择景点
function selectAttraction(id) { selectedId.value = id }

function openAttractionDetails(place) {
    detailPlace.value = place
    detailVisible.value = true
    void recordDetailView({
        account: account.value ?? accountReady.value,
        targetType: 'attraction',
        targetId: place.id
    })
}

// Google Maps 导航
function googleMapsUrl(place) {
    return `https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lng}`
}

function buildAttractionParams() {
    const params = new URLSearchParams()

    if (keyword.value.trim()) { params.set('q', keyword.value.trim()) }
    if (region.value) { params.set('region', region.value) }
    if (category.value) { params.set('category', category.value) }
    if (theme.value) { params.set('theme', theme.value) }
    if (lessKnownOnly.value) { params.set('less_known', '1') }

    return params
}

// 根据最后一次成功查询生成导出地址
const exportUrl = computed(() => {
    const query = appliedQuery.value

    if (query === null) {
        return ''
    }

    return query
        ? `/api/attractions/export/?${query}`
        : '/api/attractions/export/'
})

// 获取完整景点目录，不使用任何筛选条件
async function loadAllAttractions() {
    try {
        const response = await fetch('/api/attractions/')
        if (!response.ok) { throw new Error(`HTTP ${response.status}`) }

        const data = await response.json()
        allAttractions.value = data.items || []
    } catch (err) {
        console.error('获取完整景点目录失败:', err)
    }
}

// 从 Django 获取景点
async function loadAttractions() {
    // 避免重复发送请求
    if (loading.value) return

    loading.value = true
    error.value = ''

    const params = buildAttractionParams()
    const query = params.toString()

    const url = query  ? `/api/attractions/?${query}` : '/api/attractions/'
    try {
        const response = await fetch(url)

        if (!response.ok) {throw new Error(`HTTP ${response.status}`)}
        const data = await response.json()

        // 更新景点列表
        attractions.value = data.items || []
        appliedQuery.value = query   // 保存本次成功查询的参数

        // 如果筛选后景点不存在，清除原来的选择
        if (!attractions.value.some(place => place.id === selectedId.value)) {
            selectedId.value = null
        }
    } catch (err) {
        error.value = err.message || '获取景点失败'
    } finally {
        loading.value = false
    }
}

// 重置筛选
function resetFilters() {
    keyword.value = ''
    region.value = ''
    category.value = ''
    theme.value = ''
    lessKnownOnly.value = false
    loadAttractions()
}

// 获取当前登录用户
async function loadAccount() {
    try {
        const response = await fetch('/api/account/', {
            method: 'GET'
        })

        if (!response.ok) { throw new Error('获取用户信息失败') }
        account.value = await response.json()
        const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
        csrfToken.value = cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
    } catch (err) {
        accountError.value = true
        console.error(err)
    }
    return account.value
}

// 页面加载后获取数据
onMounted(() => {
    loadAllAttractions()
    loadAttractions()
    accountReady.value = loadAccount()
})

</script>

<template>
    <el-container direction="vertical">
        <el-header class="site-header" height="auto">
            <div class="brand">
                <span class="brand-icon">澳</span>
                <div><h2>澳門漫遊</h2><small>MACAO CULTURAL GUIDE</small></div>
            </div>
            <el-menu :default-active="activePage" mode="horizontal" :ellipsis="false" class="site-nav"
                @select="activePage = $event">
                <el-menu-item index="attractions">景点探索</el-menu-item>
                <el-menu-item index="discovery">美食与文创</el-menu-item>
                <el-menu-item index="bookmarks">我的收藏</el-menu-item>
                <el-menu-item index="planner">行程规划</el-menu-item>
            </el-menu>
            <el-space wrap>
                <el-text v-if="accountError" type="danger">登录状态获取失败</el-text>
                <template v-else-if="account?.authenticated">
                    <span>你好，{{ account.account }}</span>
                    <el-link v-if="account.staff" href="http://127.0.0.1:8008/admin/" target="_blank"
                        rel="noopener noreferrer">管理后台</el-link>
                    <form method="post" action="/accounts/logout/">
                        <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken">
                        <el-button native-type="submit">退出登录</el-button>
                    </form>
                </template>
                <template v-else-if="account">
                    <el-link href="/accounts/login/?next=/">登录</el-link>
                    <el-link href="/accounts/register/?next=/">注册</el-link>
                </template>
                <el-text v-else type="info">正在检查登录状态...</el-text>
            </el-space>
        </el-header>

        <el-main class="site-main">
            <section class="hero">
                <p class="eyebrow">DISCOVER MACAO</p>
                <h1 v-if="activePage === 'attractions'">在澳门，发现城市的另一面。</h1>
                <h1 v-else-if="activePage === 'discovery'">从街头味道到澳门手信。</h1>
                <h1 v-else-if="activePage === 'planner'">规划属于你的澳门漫步。</h1>
                <h1 v-else>收藏你的澳门记忆。</h1>
                <p v-if="activePage === 'attractions'">从世界文化遗产到城市街巷，探索澳门独特的历史、文化与生活。</p>
                <p v-else-if="activePage === 'discovery'">从街头美食到特色手信，发现澳门独特的本地生活与城市风味。</p>
                <p v-else-if="activePage === 'planner'">根据你的兴趣与时间预算，生成个性化的澳门步行行程。</p>
                <p v-else>查看和管理你收藏的景点、美食与澳门手信。</p>
            </section>

            <template v-if="activePage === 'attractions'">
                <el-card shadow="never">
                    <el-form label-position="top" @submit.prevent="loadAttractions">
                        <el-row :gutter="16">
                            <el-col :xs="24" :sm="12" :lg="8">
                                <el-form-item label="搜索景点">
                                    <el-input v-model="keyword" type="search" placeholder="输入景点名称、英文名称或地址" clearable />
                                </el-form-item>
                            </el-col>
                            <el-col :xs="24" :sm="12" :lg="6">
                                <el-form-item label="选择区域">
                                    <el-select v-model="region" :empty-values="[null, undefined]">
                                        <el-option v-for="item in regions" :key="item.value" :label="item.label" :value="item.value" />
                                    </el-select>
                                </el-form-item>
                            </el-col>
                            <el-col :xs="24" :sm="12" :lg="5">
                                <el-form-item label="选择分类">
                                    <el-select v-model="category" :empty-values="[null, undefined]">
                                        <el-option v-for="item in categories" :key="item.value" :label="item.label" :value="item.value" />
                                    </el-select>
                                </el-form-item>
                            </el-col>
                            <el-col :xs="24" :sm="12" :lg="5">
                                <el-form-item label="选择观光主题">
                                    <el-select v-model="theme" :empty-values="[null, undefined]">
                                        <el-option v-for="item in themes" :key="item.value" :label="item.label" :value="item.value" />
                                    </el-select>
                                </el-form-item>
                            </el-col>
                        </el-row>
                        <el-space wrap>
                            <el-checkbox v-model="lessKnownOnly">只看小众景点</el-checkbox>
                            <el-button type="primary" native-type="submit" :loading="loading">搜索</el-button>
                            <el-button :disabled="loading" @click="resetFilters">重置</el-button>
                        </el-space>
                    </el-form>
                </el-card>

                <section class="page-section">
                    <div class="section-heading">
                        <div><p class="eyebrow">MACAO MAP</p><h2>地图探索</h2></div>
                        <el-text type="info">点击地图标记查看景点</el-text>
                    </div>
                    <AttractionMap :places="attractions" :selected-id="selectedId" @select="selectAttraction" />
                    <el-card v-if="selectedPlace" shadow="never" class="section-gap">
                        <strong>{{ selectedPlace.name }}</strong>
                        <p>{{ selectedPlace.address }}</p>
                        <el-space wrap>
                            <el-link :href="googleMapsUrl(selectedPlace)" target="_blank" rel="noopener noreferrer">Google Maps 导航 ↗</el-link>
                            <el-button @click="selectedId = null">取消选择</el-button>
                        </el-space>
                    </el-card>
                </section>

                <section class="page-section">
                    <div class="section-heading">
                        <div><p class="eyebrow">THE ATTRACTIONS</p><h2>探索景点</h2></div>
                        <el-space wrap>
                            <el-text type="info">{{ attractions.length }} 个景点</el-text>
                            <el-link v-if="exportUrl && !loading && !error" :href="exportUrl" type="primary">导出当前结果 ↓</el-link>
                        </el-space>
                    </div>
                    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
                    <div v-loading="loading" element-loading-text="正在加载景点..." class="loading-region">
                        <el-row v-if="!error && attractions.length" :gutter="20" class="card-row">
                            <el-col v-for="place in attractions" :key="place.id" :xs="24" :sm="12" :lg="8">
                                <el-card shadow="hover" :class="['content-card', { 'is-selected': selectedId === place.id }]">
                                    <el-image v-if="place.image_url" :src="place.image_url" :alt="place.name" fit="cover" loading="lazy" class="card-image" />
                                    <el-space wrap>
                                        <el-tag>{{ place.category_label }}</el-tag>
                                        <el-tag type="info">{{ place.region_label }}</el-tag>
                                    </el-space>
                                    <h3>{{ place.name }}</h3>
                                    <el-text v-if="place.name_en" type="info" size="small">{{ place.name_en }}</el-text>
                                    <p class="summary">{{ place.summary }}</p>
                                    <el-descriptions :column="1" size="small">
                                        <el-descriptions-item label="地址">{{ place.address }}</el-descriptions-item>
                                        <el-descriptions-item label="开放时间">{{ place.hours }}</el-descriptions-item>
                                        <el-descriptions-item label="门票">{{ place.admission }}</el-descriptions-item>
                                    </el-descriptions>
                                    <el-space wrap>
                                        <el-tag type="info" size="small">{{ place.visit_minutes }} 分钟</el-tag>
                                        <el-tag v-for="topic in place.sight_topics" :key="topic.id" type="info" size="small">{{ topic.name }}</el-tag>
                                        <el-tag v-if="place.less_known" type="warning" size="small">小众景点</el-tag>
                                    </el-space>
                                    <el-space wrap class="section-gap">
                                        <el-button type="primary" @click="openAttractionDetails(place)">查看详情</el-button>
                                        <el-button @click="selectAttraction(place.id)">地图定位</el-button>
                                    </el-space>
                                </el-card>
                            </el-col>
                        </el-row>
                        <el-empty v-else-if="!loading && !error" description="暂时没有找到景点，请调整搜索条件。" />
                    </div>
                </section>
            </template>
            <LocalListings v-else-if="activePage === 'discovery'" :attractions="allAttractions" :account="account" :account-ready="accountReady" />
            <ItineraryPlanner v-else-if="activePage === 'planner'" :categories="categories" :account="account" />
            <MyBookmarks v-else />
        </el-main>

        <el-dialog v-model="detailVisible" :title="detailPlace?.name" width="min(640px, 92vw)">
            <template v-if="detailPlace">
                <el-image v-if="detailPlace.image_url" :src="detailPlace.image_url" :alt="detailPlace.name" fit="cover" class="detail-image" />
                <p v-if="detailPlace.name_en"><el-text type="info">{{ detailPlace.name_en }}</el-text></p>
                <p>{{ detailPlace.summary }}</p>
                <p v-if="detailPlace.history">{{ detailPlace.history }}</p>
                <el-space wrap>
                    <el-tag v-for="tag in detailPlace.tag_labels" :key="tag">{{ tag }}</el-tag>
                </el-space>
                <el-divider />
                <el-descriptions :column="1">
                    <el-descriptions-item label="地址">{{ detailPlace.address }}</el-descriptions-item>
                    <el-descriptions-item label="开放时间">{{ detailPlace.hours }}</el-descriptions-item>
                    <el-descriptions-item label="门票">{{ detailPlace.admission }}</el-descriptions-item>
                    <el-descriptions-item label="建议停留">{{ detailPlace.visit_minutes }} 分钟</el-descriptions-item>
                </el-descriptions>
                <el-space wrap>
                    <el-link v-if="detailPlace.source_url" :href="detailPlace.source_url" target="_blank" rel="noopener noreferrer">查看资料来源 ↗</el-link>
                    <el-link :href="googleMapsUrl(detailPlace)" target="_blank" rel="noopener noreferrer">Google Maps 导航 ↗</el-link>
                </el-space>
            </template>
        </el-dialog>
        <el-footer class="site-footer">澳門漫遊 · MACAO CULTURAL GUIDE</el-footer>
    </el-container>
</template>
