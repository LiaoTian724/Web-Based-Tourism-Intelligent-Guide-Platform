<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
    categories: {type: Array, required: true}
})

// 从 App.vue 传入的分类中排除“全部分类”
const interestOptions = computed(() =>props.categories.filter(item => item.value))

// 用户输入
const interests = ref([])
const budgetMinutes = ref(180)

// 页面状态
const loading = ref(false)
const error = ref('')
const trip = ref(null)

// 获取 Django CSRF Token
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))

    return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
}

// 生成规则行程
async function generatePlan() {
    if (loading.value) return

    loading.value = true
    error.value = ''
    trip.value = null

    try {
        let csrfToken = getCsrfToken()

        // 若尚未取得 CSRF Cookie，先请求已有的账户接口
        if (!csrfToken) {
            const accountResponse = await fetch('/api/account/')

            if (!accountResponse.ok) {throw new Error('无法初始化请求，请刷新页面')}
            csrfToken = getCsrfToken()
        }

        if (!csrfToken) {throw new Error('无法获取 CSRF Token')}

        const response = await fetch('/api/itineraries/plan/', {
            method: 'POST',  credentials: 'same-origin',
            headers: {'Content-Type': 'application/json',  'X-CSRFToken': csrfToken},
            body: JSON.stringify({interests: interests.value, budget_minutes: Number(budgetMinutes.value)})
        })

        const data = await response.json().catch(() => null)

        if (!response.ok) {throw new Error(data?.error || `HTTP ${response.status}`)}
        if (!Array.isArray(data?.stops)) {throw new Error('服务器返回的行程格式不正确')}

        trip.value = data

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
            <form class="plan-panel" @submit.prevent="generatePlan">
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
                    </template>

                    <p v-else> 当前时间预算无法安排景点，请增加可用时间。</p>
                </template>

                <p v-else class="hint">  选择兴趣和可用时间后，点击生成行程。 </p>
            </div>

        </div>
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
</style>
