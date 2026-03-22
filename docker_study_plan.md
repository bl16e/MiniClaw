# Docker 学习计划

## 阶段一：基础入门（3天）
1. **Docker 核心概念**
   - 容器 vs 虚拟机
   - 镜像/容器/仓库关系
2. **环境搭建**
   - 安装 Docker Desktop / Docker Engine
   - 验证安装：`docker --version` & `docker run hello-world`
3. **基础命令实践**
   - 镜像操作：pull/build/push
   - 容器操作：run/start/stop/remove

## 阶段二：进阶应用（5天）
1. **Dockerfile 深度实践**
   - 多阶段构建优化
   - 指令最佳实践（如 COPY vs ADD）
2. **数据管理**
   - Volume 与 Bind Mount 对比
   - 持久化数据库容器数据
3. **网络配置**
   - 自定义网络创建
   - 容器间通信实验

## 阶段三：生产级应用（4天）
1. **Docker Compose**
   - 编写多容器应用配置文件
   - 服务依赖与健康检查
2. **实战项目**
   - 部署 Flask + MySQL 应用
   - 容器化现有 Node.js 项目
3. **优化技巧**
   - 镜像体积压缩
   - CI/CD 集成基础

## 每日学习建议
- 上午：理论学习（官方文档+视频教程）
- 下午：实操练习（每学完1个知识点完成1个小实验）
- 晚上：整理笔记+提交实验代码到 GitHub

> 学习资源推荐：
> 1. Docker 官方文档（https://docs.docker.com）
> 2. 《Docker 从入门到实践》开源书
> 3. Udemy 课程 "Docker Mastery"