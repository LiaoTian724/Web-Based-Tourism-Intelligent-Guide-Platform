<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
    places: {
        type: Array,
        default: () => []
    },
    selectedId: {
        type: Number,
        default: null
    }
})

const emit = defineEmits(['select'])

const mapElement = ref(null)

let map = null
let markerLayer = null

const markers = new Map()

// 创建景点弹窗
function createPopup(place) {
    // <div>
    //     <strong>大三巴牌坊</strong>
    //     <p>澳门大三巴街</p>
    // </div>  
    const box = document.createElement('div')

    const name = document.createElement('strong')
    name.textContent = place.name

    const address = document.createElement('p')
    address.textContent = place.address

    box.append(name, address)

    return box
}



// 更新地图标记
function renderMarkers() {
    if (!markerLayer) return

    markerLayer.clearLayers()
    markers.clear()

    props.places.forEach((place, index) => {
        const lat = place.lat
        const lng = place.lng

        // 检查经纬度
        if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) return

        // 创建编号标记
        const marker = L.marker([lat, lng], {
            title: place.name,

            icon: L.divIcon({
                className: 'attraction-pin',
                html: `<span>${index + 1}</span>`,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            })
        }).addTo(markerLayer)

        // 添加景点信息
        marker.bindPopup(createPopup(place))

        // 点击标记，通知父组件
        marker.on('click', () => {emit('select', place.id)})
        markers.set(place.id, marker)
    })

    // 自动调整地图范围
    const points = [...markers.values()].map(
        marker => marker.getLatLng()
    )

    if (points.length > 1) {
        map.fitBounds(points, {padding: [30, 30], maxZoom: 14})
    } else if (points.length === 1) {
        map.setView(points[0], 14)
    } else {
        map.setView([22.17, 113.55], 12)
    }
}

// 定位选中的景点
function focusSelected() {
    if (!map || props.selectedId === null) return

    const marker = markers.get(props.selectedId)
    if (!marker) return

    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 15))

    marker.openPopup()
}

// 初始化地图
onMounted(() => {
    map = L.map(mapElement.value, {scrollWheelZoom: false}).setView([22.17, 113.55], 12)

    // 使用 OpenStreetMap 地图数据
    L.tileLayer(
        'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        {
            maxZoom: 19,
            attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }
    ).addTo(map)

    markerLayer = L.layerGroup().addTo(map)

    renderMarkers()
    focusSelected()
})

// 景点数据发生变化时更新标记
watch(
    () => props.places,
    () => {
        renderMarkers()
        focusSelected()
    }
)

// 选中景点发生变化时定位
watch(
    () => props.selectedId,
    focusSelected
)

// 离开页面时释放地图
onUnmounted(() => {
    map?.remove()
    map = null
})
</script>

<template>
    <section class="map-card">

        <div ref="mapElement" class="map-canvas"></div>

        <p class="map-help">
            点击地图标记查看景点，也可以从景点卡片定位。
        </p>

    </section>
</template>

<style scoped>
.map-card {
    width: 100%;
    overflow: hidden;
    border-radius: 14px;
    border: 1px solid #e9e6df;
    background: white;
}

.map-canvas {
    width: 100%;
    height: 430px;
    background: #e8eeeb;
}

.map-help {
    padding: 12px 16px;
    color: #78847c;
    font-size: 12px;
}

:deep(.leaflet-container) {
    width: 100%;
    height: 100%;
    font-family: inherit;
}

:deep(.attraction-pin) {
    background: transparent;
    border: none;
}

:deep(.attraction-pin span) {
    display: grid;
    place-items: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #315d4b;
    border: 2px solid white;
    color: white;
    font-weight: bold;
    box-shadow: 0 2px 5px #0003;
}
</style>
