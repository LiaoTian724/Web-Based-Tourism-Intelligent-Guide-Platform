<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
    categories: {type: Array, required: true},
    account: {type: Object, default: null}
})

// 从 App.vue 传入的分类中排除“全部分类”
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

// 获取历史行程   GET
async function loadSavedTrips() {
    savedError.value = ''
    try {
        const response = await fetch('/api/itineraries/', {
            method: "GET",
            credentials: 'same-origin'
        })
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
    if (!Number.isInteger(budgetMinutes.value) || budgetMinutes.value < 30 || budgetMinutes.value > 480) {
        error.value = '可用时间需要是 30 至 480 之间的整数'
        return
    }

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
    <section>
        <el-row :gutter="20">
            <el-col :xs="24" :md="12" class="section-bottom">
                <el-card shadow="never">
                    <template #header><h2>设置你的行程</h2></template>
                    <el-form label-position="top" :disabled="loading" @submit.prevent="generatePlan(false)">
                        <el-form-item label="感兴趣的景点类型">
                            <el-checkbox-group v-model="interests">
                                <el-checkbox v-for="item in interestOptions" :key="item.value" :value="item.value">{{ item.label }}</el-checkbox>
                            </el-checkbox-group>
                        </el-form-item>
                        <el-form-item label="可用时间（分钟）">
                            <el-input-number v-model="budgetMinutes" :min="30" :max="480" :precision="0" :value-on-clear="180" />
                        </el-form-item>
                        <el-button type="primary" native-type="submit" :loading="loading">生成行程</el-button>
                        <p class="muted">系统根据兴趣、停留时间和预计步行时间生成路线，最多安排四个景点。</p>
                    </el-form>
                </el-card>
            </el-col>
            <el-col :xs="24" :md="12" class="section-bottom">
                <el-card v-loading="loading" shadow="never">
                    <template #header><h2>行程建议</h2></template>
                    <el-alert v-if="message" :title="message" type="success" :closable="false" show-icon />
                    <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon />
                    <template v-else-if="trip?.stops.length">
                        <p>预计总时间：<strong>{{ trip.total_minutes }} 分钟</strong></p>
                        <p class="muted">步行时间根据景点直线距离估算，不代表实际道路导航时间。</p>
                        <el-timeline>
                            <el-timeline-item v-for="(stop, index) in trip.stops" :key="stop.id"
                                :timestamp="index === 0 ? '行程起点' : `预计步行 ${stop.walk_minutes} 分钟`" placement="top">
                                <strong>{{ index + 1 }}. {{ stop.name }}</strong>
                                <p>建议停留 {{ stop.visit_minutes }} 分钟</p>
                            </el-timeline-item>
                        </el-timeline>
                        <el-space wrap>
                            <el-link v-if="trip.navigation_url" :href="trip.navigation_url" target="_blank" rel="noopener noreferrer">在 Google Maps 中查看路线</el-link>
                            <el-link v-if="account && !account.authenticated" href="/accounts/login/?next=/">登录后保存行程</el-link>
                            <el-button v-else-if="account?.authenticated && !trip.id" type="primary" :loading="loading" @click="generatePlan(true)">保存行程</el-button>
                            <el-link v-else-if="account?.authenticated && trip.id" :href="`/api/itineraries/${trip.id}/export/`" type="primary">下载 Markdown</el-link>
                        </el-space>
                    </template>
                    <el-empty v-else :description="trip ? '当前时间预算无法安排景点，请增加可用时间。' : '选择兴趣和可用时间后，点击生成行程。'" :image-size="80" />
                </el-card>
            </el-col>
        </el-row>
        <el-card v-if="account?.authenticated" shadow="never">
            <template #header><h2>我的行程</h2></template>
            <el-alert v-if="savedError" :title="savedError" type="error" :closable="false" show-icon>
                <el-button @click="loadSavedTrips">重试</el-button>
            </el-alert>
            <template v-else-if="savedTrips.length">
                <div v-for="item in savedTrips" :key="item.id">
                    <strong>{{ item.stops.map(stop => stop.name + (stop.enabled ? '' : '（已下架）')).join(' → ') }}</strong>
                    <p>{{ item.total_minutes }} 分钟</p>
                    <el-link :href="`/api/itineraries/${item.id}/export/`" type="primary">导出</el-link>
                    <el-divider />
                </div>
            </template>
            <el-empty v-else description="还没有保存的行程。" :image-size="80" />
        </el-card>
    </section>
</template>
