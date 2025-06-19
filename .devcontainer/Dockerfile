# .devcontainer/Dockerfile
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root
SHELL ["/bin/bash", "-lc"]

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Подготовка /nix и группы
RUN mkdir -m 0755 /nix \
 && groupadd --system nixbld \
 && useradd --system --no-create-home --shell /usr/sbin/nologin --gid nixbld nixbld1 \
 && chown -R vscode /nix

# 3) Переключаемся на vscode и ставим Nix
USER vscode
ENV HOME=/home/vscode
ENV USER=vscode
SHELL ["/bin/bash", "-lc"]

RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --no-daemon \
 && rm /tmp/install-nix.sh

# 4) Конфигурируем экспериментальные фичи
USER root
RUN mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf

# 5) Глобальный PATH
ENV PATH=/home/vscode/.nix-profile/bin:/home/vscode/.nix-profile/sbin:${PATH}

USER vscode
