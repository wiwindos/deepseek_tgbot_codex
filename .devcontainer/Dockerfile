# Используем официальный Dev Container с Python 3.11
FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

USER root

# 1) Устанавливаем curl, bash и сертификаты
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl bash ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 2) Скачиваем и устанавливаем Nix-демон
RUN curl -L https://releases.nixos.org/nix/latest/install -o /tmp/install-nix.sh && \
    bash /tmp/install-nix.sh --daemon && \
    rm /tmp/install-nix.sh

# 3) Настраиваем flakes и обновляем channel
RUN . /root/.nix-profile/etc/profile.d/nix.sh && \
    nix-channel --update && \
    mkdir -p /etc/nix && \
    echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Возвращаемся на пользователя vscode и подхватываем nix в PATH
USER vscode
ENV PATH=/home/vscode/.nix-profile/bin:${PATH}
