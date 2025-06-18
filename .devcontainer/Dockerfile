# .devcontainer/Dockerfile

# 1) Базовый образ с Python 3.11
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# 2) Сразу работаем от root, чтобы ставить системные пакеты
USER root

# 3) Устанавливаем curl, bash и сертификаты
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl bash ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# 4) Используем bash для установки Nix в режиме --daemon
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -L https://releases.nixos.org/nix/latest/install \
    | bash -s -- --daemon \
 && . /root/.nix-profile/etc/profile.d/nix.sh \
 && nix-channel --update \
 && mkdir -p /etc/nix \
 && echo "experimental-features = nix-command flakes" > /etc/nix/nix.conf

# 5) Возвращаемся к vscode-пользователю и добавляем Nix в PATH
USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
