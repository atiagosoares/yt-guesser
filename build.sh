# Do everything
rm -rf build/do_everything/*
pip install -r src/do_everything/requirements.txt -t build/do_everything
cp src/do_everything/* build/do_everything

# GET videos
rm -rf build/videos_get/*
cp src/videos_get/main.py build/videos_get/main.py