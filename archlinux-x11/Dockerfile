FROM archlinux:20200908

RUN pacman -Syu --noconfirm \
    && pacman -S --noconfirm git base-devel sudo mesa-demos \
    && rm -rf /var/cache/pacman/pkg/*

RUN echo "Defaults         lecture = never" > /etc/sudoers.d/privacy \
    && echo "%wheel ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel

RUN useradd -u 2001 -m -G wheel -s /bin/bash builder

USER builder
WORKDIR /home/builder

RUN git clone https://aur.archlinux.org/yay.git \
    && cd yay \
    && makepkg -si --noconfirm \
    && sudo rm -rf /var/cache/pacman/pkg/* /home/builder/yay /home/builder/.cache
