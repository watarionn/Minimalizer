FROM python:3.11-slim
RUN apt-get update -qq \
 && apt-get install -y -qq git cmake build-essential libgl1-mesa-dev libglu1-mesa-dev \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir git+https://github.com/BachiLi/diffvg.git@85802a71fbcc72d79cb75716eb4da4392fd09532
WORKDIR /workspace
