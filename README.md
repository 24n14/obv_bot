## Start
### Config
1. Перед началом использования бота создайте дубликат config_example.ini
2. Переименуйте дубликат в config.ini 
2. Заполните поля API ключей Bybit
3. Введите токены, которые будут торговаться:
   * BTC/USDT, BTC/USDC - спот
   * BTC/USDT:USDT, BTC/USDC:USDC - фьючерс
   * BTC/USDT:USDT-260403 - срочный фьючерс, где дата записана в формате ГГ.ММ.ДД
3. Данные индикаторов выставлены по умолчанию, их можно менять
4. Введите желаемые веса для индикаторов
5. Раздел ORDER
   * volume_const - фиксированный объем для сделки, в то случае когда не все индикаторы показывают одно и тоже значение
   * volume_percent - процент от свободных USDT на торговом аккаунте для сделок, когда все индикаторы показывают один и тот же сигнал
   * leverage - кредитное плечо для сделок на фьючерсах, например 10х, 15х, 20х и т.д.

### Docker
#### Установка
Скопируйте и вставьте в консоль по очереди
1. `sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)`
2. `sudo apt update`
3. `sudo apt install ca-certificates curl`
4. `sudo install -m 0755 -d /etc/apt/keyrings`
5. `sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc`
6. `sudo chmod a+r /etc/apt/keyrings/docker.asc`
7. `sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF`
8. `sudo apt update`
9. `sudo systemctl start docker`
10. `sudo systemctl status docker`

#### Запуск Бота
Скопируйте и вставьте в консоль по очереди
1. `git clone https://github.com/DimaTik/OBV.git`
2. `cd OBV`
3. `docker build -t bot .` - создание образа bot
4. `docker run --name bot1 bot` - запуск контейнера с именем bot1

#### Просмотр логов
`docker logs bot1`

#### Остановка бота
`docker stop bot1`

#### Удаление бота
`docker rm bot1`
