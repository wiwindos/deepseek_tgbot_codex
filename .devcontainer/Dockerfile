FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root
SHELL ["/bin/bash", "-lc"]

# 1) Системные утилиты
RUN apt-get update \
 && apt-get install -y curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 2) Создаём группу/пользователей для Nix build
RUN groupadd --system nixbld \
 && for i in $(seq 1 10); do useradd --system --gid nixbld nixbld$i; done

# 3) Установка Nix в multi-user режиме
RUN curl -fsSL https://nixos.org/nix/install -o /tmp/install-nix.sh \
 && bash /tmp/install-nix.sh --daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf \
 && rm /tmp/install-nix.sh

# 4) Экспортируем PATH, чтобы nix был сразу доступен
ENV PATH=/root/.nix-profile/bin:/root/.nix-profile/sbin:${PATH}

USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
