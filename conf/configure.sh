ROOT="/home/alex/proj/rclone"
sudo ln -s $ROOT/conf/nginx.conf /etc/nginx/sites-enabled/
mkdir logs
touch $ROOT/logs/access.log
touch $ROOT/logs/error.log
