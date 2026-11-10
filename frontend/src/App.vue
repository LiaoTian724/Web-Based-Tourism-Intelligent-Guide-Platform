<script setup>
import { ref, onMounted } from 'vue'

// 景点数据
const attractions = ref([])

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

// 页面加载后自动获取数据
onMounted(loadAttractions)
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

            <div class="header-right">探索澳门 · 感受文化</div>
        </header>

        <main class="container">

            <section class="hero">
                <p class="eyebrow">DISCOVER MACAO</p>

                <h1>在澳门，发现城市的另一面。</h1>

                <p>
                    从世界文化遗产到城市街巷，
                    探索澳门独特的历史、文化与生活。
                </p>
            </section>

            <!-- 搜索和筛选 -->
            <section class="search-panel">

                <form @submit.prevent="loadAttractions">

                    <label>
                        <span>搜索景点</span>

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
                            <option v-for="item in categories" :key="item.value" :value="item.value">{{ item.label }}
                            </option>
                        </select>
                    </label>

                    <div class="actions">
                        <button type="submit">搜索</button>
                        <button type="button" class="reset" @click="resetFilters">重置</button>
                    </div>

                </form>

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
                    <article v-for="place in attractions" :key="place.id" class="place-card">
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
                        </div>
                    </article>
                </div>

                <div v-else class="message">暂时没有找到景点，请调整搜索条件。</div>
            </section>

        </main>

        <footer>澳門漫遊 · MACAO CULTURAL GUIDE</footer>

    </div>
</template>
