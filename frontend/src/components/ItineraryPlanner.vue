
<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
    categories: {type: Array, required: true},
    account: {type: Object, default: null}
})

// 从 App.vue 传入的分类中排除“全部分类”
// 从父组件传入的景点分类数组 categories 中，过滤掉 value 为空的选项，生成一个可以自动更新的兴趣选项列表 interestOptions
const interestOptions = computed(() => props.categories.filter(item => item.value))

const interests = ref([])
const budgetMinutes = ref(180)

// 页面状态
const loading = ref(false)
const error = ref('')
const message = ref('')
const trip = ref(null)

const savedTrips = ref([])
const savedError = ref('')


function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
}


// 获取历史行程
async function loadSavedTrips() {
    savedError.value = ''
    try {
        const response = await fetch('/api/itineraries/', {credentials: 'same-origin'})
        const data = await response.json().catch(() => null)

        if (!response.ok) {throw new Error(data?.error || '获取历史行程失败')}
        savedTrips.value = data.items || []
    } catch (err) {
        savedError.value = err.message
    }
}



// 登录状态变化时加载历史行程
watch(
    () => props.account?.authenticated,
    authenticated => {
        if (authenticated) {
            loadSavedTrips()
        } else {
            savedTrips.value = []
        }
    },
    { immediate: true }  // 注册时先执行一次，以后数据变化时继续执行
)


// 生成或保存行程   POST
async function generatePlan(save = false) {
    if (loading.value) return

    if (save && !props.account?.authenticated) {
        error.value = '请登录后保存行程'
        return
    }
    if (save && !trip.value?.stops.length) {return}

    loading.value = true
    error.value = ''
    message.value = ''
    if (!save) {trip.value = null}

    try {
        let csrfToken = getCsrfToken()
        if (!csrfToken) {
            await fetch('/api/account/')
            csrfToken = getCsrfToken()
        }
        if (!csrfToken) {throw new Error('无法获取 CSRF Token')}

        const payload = {
            interests: interests.value,
            budget_minutes: Number(budgetMinutes.value),
            save: save
        }
        if (save) {
            payload.stop_ids = trip.value.stops.map(stop => stop.id)        // 动态添加 stop_ids 属性
        }

        const response = await fetch('/api/itineraries/plan/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
            body: JSON.stringify(payload)
        })

        const data = await response.json().catch(() => null)
        if (!response.ok) {
            throw new Error(data?.error || '请求失败')
        }

        trip.value = data

        if (save && data.id) {
            message.value = '行程已保存'
            await loadSavedTrips()
        } 
    } catch (err) {
        error.value = err.message || '生成行程失败'
    } finally {
        loading.value = false
    }
}


</script>






<template>
    <section class="planner-page">
        <div class="planner-layout">

            <!-- 左侧：用户输入 -->
            <form class="plan-panel" @submit.prevent="generatePlan(false)">
                <h2>设置你的行程</h2>

                <fieldset :disabled="loading">
                    <legend>感兴趣的景点类型</legend>

                    <label v-for="item in interestOptions" :key="item.value" class="interest-option">
                        <input v-model="interests" type="checkbox" :value="item.value">{{ item.label }}
                    </label>
                </fieldset>

                <label class="budget-label" for="budget"> 可用时间（分钟）</label>
                <input id="budget" v-model.number="budgetMinutes" type="number" min="30" max="480" required :disabled="loading">
                <button type="submit" :disabled="loading">{{ loading ? '正在生成...' : '生成行程' }}</button>
                <p class="hint"> 系统根据兴趣、停留时间和预计步行时间生成路线，最多安排四个景点。</p>
            </form>

            <!-- 右侧：结果 -->
            <div class="plan-panel">
                <h2>行程建议</h2>
                <p v-if="message" role="status">{{ message }}</p>
                <p v-if="error" class="plan-error" role="alert">{{ error }}</p>

                <template v-else-if="trip">
                    <template v-if="trip.stops.length">
                        <p class="plan-total">预计总时间：<strong>{{ trip.total_minutes }} 分钟</strong></p>

                        <p class="hint">步行时间根据景点直线距离估算，不代表实际道路导航时间。</p>

                        <ol class="plan-stops">
                            <li v-for="(stop, index) in trip.stops" :key="stop.id">
                                <strong>{{ index + 1 }}. {{ stop.name }}</strong>

                                <p>{{ index === 0 ? '行程起点' : `预计步行 ${stop.walk_minutes} 分钟`}}</p>
                                <p>建议停留 {{ stop.visit_minutes }} 分钟</p>
                            </li>
                        </ol>

                        <a v-if="trip.navigation_url" class="plan-navigation" :href="trip.navigation_url" target="_blank" rel="noopener noreferrer">
                            在 Google Maps 中查看路线
                        </a>

                        <div v-if="trip?.stops?.length" class="plan-actions">
                            <!-- 未登录 -->
                            <a v-if="props.account && !props.account.authenticated" href="/accounts/login/?next=/">
                                登录后保存行程
                            </a>

                            <!-- 已登录，尚未保存 -->
                            <button v-else-if="props.account?.authenticated && !trip.id"
                                type="button" :disabled="loading"  @click="generatePlan(true)"
                            >
                                {{ loading ? '正在保存...' : '保存行程' }}
                            </button>

                            <!-- 已登录，已经保存 -->
                            <a v-else-if="props.account?.authenticated && trip.id" :href="`/api/itineraries/${trip.id}/export/`">
                                下载 Markdown
                            </a>
                        </div>
                    </template>

                    <p v-else> 当前时间预算无法安排景点，请增加可用时间。</p>
                </template>

                <p v-else class="hint">  选择兴趣和可用时间后，点击生成行程。 </p>
            </div>

        </div>

        <section v-if="props.account?.authenticated" class="plan-panel saved-panel">
            <h2>我的行程</h2>
            <p v-if="savedError" class="plan-error">
                {{ savedError }}
                <button @click="loadSavedTrips">重试</button>
            </p>

            <p v-else-if="!savedTrips.length">还没有保存的行程。</p>
            <ul v-else class="saved-list">
                <li v-for="item in savedTrips" :key="item.id">
                    <div>
                        <strong>
                            {{item.stops.map(stop => stop.name + (stop.enabled ? '' : '（已下架）')).join(' → ')}}
                        </strong>
                        <p>{{ item.total_minutes }} 分钟</p>
                    </div>

                    <a :href="`/api/itineraries/${item.id}/export/`">导出</a>
                </li>
            </ul>
        </section>
    </section>
</template>



<style scoped>
.planner-page {
    padding: 20px 0 50px;
}

.planner-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 22px;
    align-items: start;
}

.plan-panel {
    padding: 24px;
    background: white;
    border: 1px solid #e9e6df;
    border-radius: 16px;
}

.plan-panel h2 {
    margin: 0 0 24px;
}

.plan-panel fieldset {
    border: 0;
    padding: 0;
    margin: 0 0 24px;
}

.plan-panel legend {
    font-weight: bold;
    margin-bottom: 14px;
}

.interest-option {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    cursor: pointer;
}

.interest-option input {
    width: 18px;
    height: 18px;
}

.budget-label {
    display: block;
    margin-bottom: 10px;
}

.plan-panel input[type="number"] {
    width: 100%;
    margin-bottom: 18px;
}

.plan-panel button {
    width: 100%;
}

.hint {
    margin-top: 16px;
    color: #78847c;
    font-size: 13px;
    line-height: 1.7;
}

.plan-total {
    margin-bottom: 16px;
}

.plan-stops {
    padding-left: 0;
    list-style: none;
}

.plan-stops li {
    padding: 15px 0;
    border-bottom: 1px solid #e9e6df;
}

.plan-stops li p {
    margin: 8px 0 0;
    color: #78847c;
    font-size: 13px;
}

.plan-error {
    color: #b42318;
}

.plan-navigation {
    display: block;
    margin-top: 20px;
    padding: 13px;
    text-align: center;
    background: #315d4b;
    color: white;
    border-radius: 8px;
    text-decoration: none;
}

@media (max-width: 750px) {
    .planner-layout {
        grid-template-columns: 1fr;
    }
}


.plan-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 18px;
}

.plan-actions button {
    flex: 1;
}

.plan-actions a {
    flex: 1;
    padding: 12px;
    text-align: center;
    border-radius: 8px;
    background: #edf3ed;
    color: #315d4b;
    text-decoration: none;
}

.saved-panel {
    margin-top: 22px;
}

.saved-list {
    list-style: none;
    padding: 0;
}

.saved-list li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 16px 0;
    border-bottom: 1px solid #e9e6df;
}

.saved-list li p {
    margin-top: 8px;
    color: #78847c;
    font-size: 13px;
}

.saved-list a {
    color: #315d4b;
    white-space: nowrap;
}


</style>
