cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN
conda activate WebDesign
python manage.py check
python manage.py migrate
python manage.py runserver 127.0.0.1:8008



cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN/frontend
npm run dev



python -m pip install "Django==6.1.3"

python -m django startproject djangovue .
python manage.py startapp backend



cd /Volumes/E_disk/Project/MACAU_TOURISM_DESIGN
npm create vite@latest frontend -- --template vue
cd frontend
npm install