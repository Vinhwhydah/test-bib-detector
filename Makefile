run:
	pip3 install -r requirements.txt
	uvicorn main:app

docker-up-dev:
	docker build -t asia-southeast1-docker.pkg.dev/system-dev-3749090/bib-wizards-dev/detector:latest .
	docker rm -f bib-detector && docker run -d --name bib-detector -p 8111:8080 asia-southeast1-docker.pkg.dev/system-dev-3749090/bib-wizards-dev/detector:latest

docker-build-pipeline-dev:
	docker build -t asia-southeast1-docker.pkg.dev/system-dev-3749090/bib-wizards-dev/detector:$GIT_COMMIT .
	docker push asia-southeast1-docker.pkg.dev/system-dev-3749090/bib-wizards-dev/detector:$GIT_COMMIT
