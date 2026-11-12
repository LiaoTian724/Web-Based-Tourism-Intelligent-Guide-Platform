<script setup>
import { ref, onMounted, computed } from 'vue'
import AttractionMap from './components/AttractionMap.vue'
import LocalListings from './components/LocalListings.vue'
import MyBookmarks from './components/MyBookmarks.vue'

// 景点数据
const attractions = ref([])
const activePage = ref('attractions')

// 用户信息
const account = ref(null)
const csrfToken = ref('')
const accountError = ref(false)




// 搜索条件
const keyword = ref('')
const region = ref('')
const category = ref('')

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

// 当前选中的景点
const selectedId = ref(null)

// 根据 ID 找到景点
const selectedPlace = computed(() => {
    return attractions.value.find(place => place.id === selectedId.value) || null
})

// 选择景点
function selectAttraction(id) { selectedId.value = id }

// Google Maps 导航
function googleMapsUrl(place) {
    return `https://www.google.com/maps/search/?api=1&query=${place.lat},${place.lng}`
}


// 从 Django 获取景点
async function loadAttractions() {
    loading.value = true
    error.value = ''

    // 构建 URL 参数
    const params = new URLSearchParams()

    if (keyword.value.trim()) { params.set('q', keyword.value.trim()) }
    if (region.value) { params.set('region', region.value) }
    if (category.value) { params.set('category', category.value) }

    const query = params.toString()
    const url = query ? `/api/attractions/?${query}` : '/api/attractions/'

    try {
        const response = await fetch(url)
        if (!response.ok) { throw new Error(`HTTP ${response.status}`) }

        const data = await response.json()

        attractions.value = data.items || []

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

    loadAttractions()
}


// 获取当前登录用户
async function loadAccount() {
    try {
        const response = await fetch('/api/account/')

        if (!response.ok) {throw new Error('获取用户信息失败')}
        account.value = await response.json()

        const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))

        csrfToken.value = cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
    } catch (err) {
        accountError.value = true
        console.error(err)
    }
}

// 页面加载后获取数据
onMounted(() => {
    loadAttractions()
    loadAccount()
})



</script>

<template>
    <div class="page">

        <header class="header">
            <div class="brand">
                <div class="brand-icon">澳</div>

                <div>
                    <h2>澳門漫遊</h2>
                    <span>MACAO CULTURAL GUIDE</span>
                </div>
            </div>

            <nav class="main-nav">
                <button :class="{ active: activePage === 'attractions' }" @click="activePage = 'attractions'">景点探索</button>
                <button :class="{ active: activePage === 'discovery' }" @click="activePage = 'discovery'">美食与文创</button>
                <button :class="{ active: activePage === 'bookmarks' }" @click="activePage = 'bookmarks'">我的收藏</button>
            </nav>

            <!-- 用户登录状态 -->
            <div class="header-account">
                <span v-if="accountError">登录状态获取失败</span>
                <template v-else-if="account?.authenticated">
                    <span>你好，{{ account.account }}</span>

                    <a v-if="account.staff" href="http://127.0.0.1:8008/admin/" target="_blank" rel="noopener noreferrer">管理后台</a>

                    <form method="post" action="/accounts/logout/">
                        <input type="hidden"  name="csrfmiddlewaretoken" :value="csrfToken">
                        <button type="submit">退出登录</button>
                    </form>
                </template>

                <template v-else-if="account">
                    <a href="/accounts/login/?next=/">登录</a>
                    <a href="/accounts/register/?next=/">注册</a>
                </template>

                <span v-else>正在检查登录状态...</span>
            </div>

        </header>

        <main class="container">

            <section class="hero">
                <p class="eyebrow">DISCOVER MACAO</p>

                <h1 v-if="activePage === 'attractions'">在澳门，发现城市的另一面。</h1>
                <h1 v-else-if="activePage === 'discovery'"> 从街头味道到澳门手信。 </h1>
                <h1 v-else>收藏你的澳门记忆。</h1>

                <p v-if="activePage === 'attractions'">从世界文化遗产到城市街巷，探索澳门独特的历史、文化与生活。</p>
                <p v-else-if="activePage === 'discovery'">从街头美食到特色手信，发现澳门独特的本地生活与城市风味。</p>
                <p v-else>查看和管理你收藏的景点、美食与澳门手信。</p>
            </section>

            <!-- 搜索和筛选 -->
            <template v-if="activePage === 'attractions'">
                <section class="search-panel">

                    <form @submit.prevent="loadAttractions">
                        <label><span>搜索景点</span>
                            <input v-model="keyword" type="search" placeholder="输入景点名称、英文名称或地址" />
                        </label>

                        <label>
                            <span>选择区域</span>
                            <select v-model="region">
                                <option v-for="item in regions" :key="item.value" :value="item.value">{{ item.label }}
                                </option>
                            </select>
                        </label>

                        <label>
                            <span>选择分类</span>
                            <select v-model="category">
                                <option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label
                                    }}</option>
                            </select>
                        </label>

                        <div class="actions">
                            <button type="submit">搜索</button>
                            <button type="button" class="reset" @click="resetFilters">重置</button>
                        </div>
                    </form>

                </section>

                <!-- 澳门地图 -->
                <section class="map-section">
                    <div class="section-title">
                        <div>
                            <p>MACAO MAP</p>
                            <h2>地图探索</h2>
                        </div>

                        <span>点击地图标记查看景点</span>
                    </div>

                    <AttractionMap :places="attractions" :selected-id="selectedId" @select="selectAttraction" />

                    <!-- 当前选中的景点 -->
                    <div v-if="selectedPlace" class="selected-place">
                        <div>
                            <strong>{{ selectedPlace.name }}</strong>
                            <p>{{ selectedPlace.address }}</p>
                        </div>

                        <div class="selected-actions">
                            <a :href="googleMapsUrl(selectedPlace)" target="_blank" rel="noopener noreferrer">Google
                                Maps 导航 ↗</a>
                            <button type="button" class="reset" @click="selectedId = null">取消选择</button>
                        </div>
                    </div>

                </section>

                <!-- 景点列表 -->
                <section class="results">
                    <div class="section-title">
                        <div>
                            <p>THE ATTRACTIONS</p>
                            <h2>探索景点</h2>
                        </div>

                        <span>{{ attractions.length }} 个景点</span>
                    </div>

                    <div v-if="loading" class="message">正在加载景点...</div>

                    <div v-else-if="error" class="message error">{{ error }}</div>

                    <div v-else-if="attractions.length" class="card-grid">
                        <article v-for="place in attractions" :key="place.id"
                            :class="['place-card', { selected: selectedId === place.id }]">
                            <div class="card-tags">
                                <span class="category">{{ place.category_label }}</span>
                                <span>{{ place.region_label }}</span>
                            </div>

                            <h3>{{ place.name }}</h3>

                            <p v-if="place.name_en" class="english">{{ place.name_en }}</p>

                            <p class="summary">{{ place.summary }}</p>

                            <div class="details">
                                <p><span>地址</span>{{ place.address }}</p>
                                <p><span>开放时间</span>{{ place.hours }}</p>
                                <p><span>门票</span>{{ place.admission }}</p>
                            </div>

                            <div class="card-footer">
                                <span>{{ place.visit_minutes }} 分钟</span>
                                <span v-if="place.world_heritage">世界遗产</span>
                                <span v-if="place.less_known">小众景点</span>
                                <button type="button" class="map-select"
                                    @click="selectAttraction(place.id)">地图定位</button>
                            </div>
                        </article>
                    </div>

                    <div v-else class="message">暂时没有找到景点，请调整搜索条件。</div>
                </section>
            </template>

            <LocalListings v-else-if="activePage === 'discovery'" :attractions="attractions"/>
            <MyBookmarks v-else />
        </main>

        <footer>澳門漫遊 · MACAO CULTURAL GUIDE</footer>
    </div>
</template>
