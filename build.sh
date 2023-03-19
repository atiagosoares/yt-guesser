# Check
rm -rf build/do_everything/*
pip install -r src/do_everything/requirements.txt -t build/do_everything
cp src/do_everything/* build/do_everything