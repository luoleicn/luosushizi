# 汉字识字卡片

面向儿童的识字卡片 Web 应用，离线拼音与常用词提示，支持多端访问与跨设备同步。

## 配置
编辑 `backend/app/core/config.yaml` 并设置强度足够的 `secret_key`。

### 账号配置
账号由后端预置，前端不提供注册。请使用 bcrypt 生成密码哈希并填入 `password_hash`。

生成 bcrypt 哈希：

```bash
python - <<'PY'
import bcrypt
pw = b"your-password"
print(bcrypt.hashpw(pw, bcrypt.gensalt()).decode())
PY
```

将输出填入 `password_hash`。

### 新增账号
编辑 `backend/app/core/config.yaml`，在 `accounts` 下新增一项：

```yaml
accounts:
  - username: "admin"
    password_hash: "<已有哈希>"
  - username: "newuser"
    password_hash: "<新哈希>"
```

修改后重启后端服务（systemd 或 uvicorn）。

## THUOCL 导入
把 THUOCL 词表文件放到 `backend/data/thuocl/`，然后执行：

```bash
python backend/app/services/dictionary/thuocl_import.py \
  --db-path backend/data/app.db \
  --thuocl-dir backend/data/thuocl
```

## 后端（FastAPI）
本项目兼容 Python 3.6.9，依赖已在 `backend/requirements.txt` 中固定版本。

### macOS 环境准备
- 安装 Python 3.6.9+（建议 3.10+，Homebrew：`brew install python`）
- 安装 Node.js 18+（建议使用 Homebrew：`brew install node`）

### Ubuntu 环境准备
- 安装 Python 3.6.9+：`sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip`
- 安装 Node.js 18+（示例）：`sudo apt-get install -y nodejs npm`

安装依赖：

```bash
pip install -r backend/requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --reload --app-dir backend
```

初始化数据库：

```bash
python -m app.core.init_db
```

## 字典迁移（单字库 -> 多用户字典）
该迁移会为每个账号创建一个私有字典“我的字库”，并把旧字库迁移进去。

```bash
python -m app.core.migrate_to_dictionaries --mode all
```

可选模式：
- `all`：把旧字库全部复制到每个用户的默认字典（默认）
- `studied`：仅复制该用户已有学习记录的汉字

迁移完成后会把旧表重命名为 `*_legacy`。

## 前端（Vue 3 + Vite）
安装依赖：

```bash
cd frontend
npm install
```

启动开发服务器：

```bash
npm run dev
```

API 基础地址（可选）：

```bash
export VITE_API_BASE=http://127.0.0.1:8000
```

### macOS 运行方法
```bash
python -m app.core.init_db
uvicorn app.main:app --reload --app-dir backend
cd frontend && npm run dev
```

### Ubuntu 运行方法
```bash
python3 -m app.core.init_db
uvicorn app.main:app --reload --app-dir backend
cd frontend && npm run dev
```

## Apache 反向代理配置（示例）
以下示例把前端与后端统一到同一域名下，后端挂载到 `/api`。

### 1) 构建前端并放置到站点目录
```bash
cd frontend
export VITE_API_BASE=/api
npm run build
```
将 `frontend/dist` 拷贝到 Apache 站点目录（示例：`/var/www/hanzi-cards`）。

### 2) 启动后端服务
建议使用 `uvicorn` 或 `gunicorn` 监听本地端口（示例 8000）。

### 3) Apache 配置示例
启用模块：
```bash
sudo a2enmod proxy proxy_http rewrite headers
```

站点配置（示例 `/etc/apache2/sites-available/hanzi-cards.conf`）：
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /var/www/hanzi-cards

    <Directory /var/www/hanzi-cards>
        AllowOverride None
        Require all granted
    </Directory>

    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8000/
    ProxyPassReverse /api/ http://127.0.0.1:8000/

    # SPA history fallback
    RewriteEngine On
    RewriteCond %{REQUEST_URI} !^/api
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteCond %{REQUEST_FILENAME} !-d
    RewriteRule ^ /index.html [L]
</VirtualHost>
```

启用站点并重载：
```bash
sudo a2ensite hanzi-cards
sudo systemctl reload apache2
```

前端环境变量提示已包含在构建步骤中。

### 静态文件缓存与压缩优化（Apache）
启用模块：
```bash
sudo a2enmod expires headers deflate
```

在站点配置中加入（或放到 `<VirtualHost>` 中）：
```apache
# 静态资源缓存
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css "access plus 30 days"
    ExpiresByType application/javascript "access plus 30 days"
    ExpiresByType application/json "access plus 7 days"
    ExpiresByType image/svg+xml "access plus 30 days"
    ExpiresByType image/png "access plus 30 days"
    ExpiresByType image/jpeg "access plus 30 days"
    ExpiresByType font/woff2 "access plus 365 days"
    ExpiresDefault "access plus 7 days"
</IfModule>

# 压缩
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain text/html text/xml text/css
    AddOutputFilterByType DEFLATE application/javascript application/json
    AddOutputFilterByType DEFLATE image/svg+xml
    Header always set Vary Accept-Encoding
</IfModule>
```

## systemd 后端服务示例（Ubuntu）
创建服务文件（示例 `/etc/systemd/system/hanzi-cards.service`）：
```ini
[Unit]
Description=Hanzi Cards Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/luosushizi/backend
Environment=HANZI_CARDS_CONFIG=/path/to/luosushizi/backend/app/core/config.yaml
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

启用并启动：
```bash
sudo systemctl daemon-reload
sudo systemctl enable hanzi-cards
sudo systemctl start hanzi-cards
sudo systemctl status hanzi-cards
```

## 可选音效
把音效文件放到 `frontend/public/sounds/`：
- `success.mp3`（认识）
- `try.mp3`（不认识）

## 接口示例
登录：

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"your-password"}'
```

鉴权校验：

```bash
curl http://127.0.0.1:8000/auth/me \
  -H 'Authorization: Bearer <token>'
```

导入汉字：

```bash
curl -X POST http://127.0.0.1:8000/dictionaries/1/characters/import \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"items":["你","好","学"]}'
```

获取学习队列：

```bash
curl http://127.0.0.1:8000/dictionaries/1/study/queue \
  -H 'Authorization: Bearer <token>'
```

提交复习：

```bash
curl -X POST http://127.0.0.1:8000/dictionaries/1/study/review \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"hanzi":"你","rating":4}'
```

开始学习会话：

```bash
curl -X POST http://127.0.0.1:8000/dictionaries/1/study/session/start \
  -H 'Authorization: Bearer <token>'
```

结束学习会话：

```bash
curl -X POST http://127.0.0.1:8000/dictionaries/1/study/session/end \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"session_id":1}'
```

汉字列表：

```bash
curl http://127.0.0.1:8000/dictionaries/1/characters/list \
  -H 'Authorization: Bearer <token>'
```

统计汇总：

```bash
curl http://127.0.0.1:8000/dictionaries/1/stats/summary \
  -H 'Authorization: Bearer <token>'
```

字典列表：

```bash
curl http://127.0.0.1:8000/dictionaries \
  -H 'Authorization: Bearer <token>'
```

创建字典：

```bash
curl -X POST http://127.0.0.1:8000/dictionaries \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"name":"我的字库","visibility":"private"}'
```
