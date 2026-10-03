FROM python:3.10-slim
ENV DIFFVG_CUDA=0
RUN apt-get update -o Acquire::Retries=2 \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git cmake build-essential ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch --extra-index-url https://download.pytorch.org/whl/cpu
RUN git clone https://github.com/BachiLi/diffvg.git /opt/diffvg \
 && cd /opt/diffvg \
 && git checkout 85802a71fbcc72d79cb75716eb4da4392fd09532 \
 && git submodule update --init pybind11 thrust \
 && mv pyproject.toml pyproject.toml.disabled \
 && pip install --no-cache-dir svgpathtools \
 && (python setup.py build_ext --inplace || true) \
 && cp build/lib.linux-x86_64-cpython-310/diffvg.so /opt/diffvg/diffvg.so \
 && test -f /opt/diffvg/diffvg.so
ENV PYTHONPATH=/opt/diffvg
WORKDIR /workspace
