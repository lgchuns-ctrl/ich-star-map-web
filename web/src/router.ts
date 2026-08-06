import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import MapView from './views/MapView.vue'
import SearchView from './views/SearchView.vue'
import DataView from './views/DataView.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView, meta: { title: '非遗星图' } },
    { path: '/map', name: 'map', component: MapView, meta: { title: '全国分布' } },
    { path: '/search', name: 'search', component: SearchView, meta: { title: '寻找一项非遗' } },
    { path: '/data', name: 'data', component: DataView, meta: { title: '数据与方法' } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title as string} · 非遗星图` : '非遗星图'
})
