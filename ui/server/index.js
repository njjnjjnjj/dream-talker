import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import history from 'connect-history-api-fallback';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 5173; // 默认使用 Vite 的端口，或者是环境变量指定的端口
const TARGET = 'http://localhost:8569'; // 后端服务地址

// 添加简单的请求日志中间件
app.use((req, res, next) => {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`[${new Date().toLocaleTimeString()}] ${req.method} ${req.originalUrl} ${res.statusCode} - ${duration}ms`);
  });
  next();
});

// 1. 配置代理 (必须在 body-parser 和 static 之前)
// 代理 /api 请求
app.use(
  '/api',
  createProxyMiddleware({
    target: TARGET,
    changeOrigin: true,
    logLevel: 'debug', // 开启调试日志
    // Express 的 app.use('/api', ...) 会自动剥离 '/api' 前缀，导致转发给后端的路径变成 '/login'
    // 而后端路由定义是 '/api/login'，所以这里需要把 '/api' 补回来
    pathRewrite: (path, req) => {
      return '/api' + path;
    },
    on: {
      error: (err, req, res) => {
        console.error('[Proxy Error]', err);
      }
    }
  })
);

// 代理 /vad WebSocket 请求
// 注意: express 本身不直接处理 ws 升级，http-proxy-middleware 可以处理
// 我们需要在 server 实例上监听 upgrade 事件，或者让 middleware 自动处理
const vadProxy = createProxyMiddleware({
  target: TARGET, // WebSocket 目标地址，http-proxy-middleware 会自动处理 ws://
  changeOrigin: true,
  ws: true, // 开启 WebSocket 代理
  logLevel: 'debug', // 开启调试日志
});
app.use('/vad', vadProxy);

// 2. 处理 SPA History 模式
// 任何不匹配静态文件的请求都会返回 index.html
app.use(history());

// 3. 托管静态文件
// 假设构建后的文件在 ui/dist 目录下
const distPath = path.resolve(__dirname, '../dist');
app.use(express.static(distPath));

// 启动服务器
const server = app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  console.log(`Proxying /api and /vad to ${TARGET}`);
});

// 手动处理 WebSocket 升级
// 虽然 http-proxy-middleware 的 ws: true 选项通常能处理
// 但在 Express 中有时需要显式绑定 upgrade 事件
server.on('upgrade', (req, socket, head) => {
  if (req.url.startsWith('/vad')) {
    vadProxy.upgrade(req, socket, head);
  }
});