import { createApp } from 'vue'
import router from './router'

import './index.css'
import LanguageProvider from './LanguageProvider.vue'

const app = createApp(LanguageProvider)

app.use(router)
app.mount('#app')
