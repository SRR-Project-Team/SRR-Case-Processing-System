
# 基础镜像（轻量版Python）
FROM python:3.11-slim

# 工作目录
WORKDIR /app

# 复制依赖清单
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt  # --no-cache-dir减少体积

# 复制代码
COPY . .

# 暴露端口（如Flask默认5000）
EXPOSE 8001 3000

# 启动命令（Django需改为：python manage.py runserver 0.0.0.0:8000）
CMD ["python", "start.py"]