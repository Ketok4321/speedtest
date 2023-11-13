<img src="data/icons/hicolor/scalable/apps/xyz.ketok.Speedtest.svg" align="left"/>

# Speedtest
A graphical [librespeed](https://librespeed.org) client written using gtk4 + libadwaita

<img src="https://gowno.ketok.xyz/screenshots/speedtest/1.png?" width="722">
<img src="https://gowno.ketok.xyz/screenshots/speedtest/2.png?" width="722">

## Instalation
### Flatpak
<a href='https://flathub.org/apps/xyz.ketok.Speedtest'><img width='200' alt='Download on Flathub' src='https://dl.flathub.org/assets/badges/flathub-badge-en.png'/></a>

## Building
### GNOME Builder
TODO

### Command-line
1. Install flatpak builder
`flatpak install flathub org.flatpak.Builder -y`
2. Build
`flatpak run org.flatpak.Builder --force-clean --user --install builddir xyz.ketok.Speedtest.yml`
3. Speedtest is now installed on your system, you can run it by running `flatpak run xyz.ketok.Speedtest`
