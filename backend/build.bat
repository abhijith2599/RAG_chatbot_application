@echo off
SETLOCAL

echo ====================================
echo Building RAG Chatbot Backend Service
echo ====================================

:: Set environment variables
set DOCKER_USERNAME=abhijithd
set REPO_NAME=rag_chatbot
set IMAGE_TAG=latest

:: Stop and remove existing containers
echo Cleaning up existing containers...
docker ps -q --filter "name=%REPO_NAME%" | findstr . && (
    docker stop %REPO_NAME%
    docker rm %REPO_NAME%
)

:: Remove existing image
echo Removing old image if exists...
docker images %DOCKER_USERNAME%/%REPO_NAME%:%IMAGE_TAG% -q | findstr . && (
    docker rmi %DOCKER_USERNAME%/%REPO_NAME%:%IMAGE_TAG%
)

:: Build new image using Dockerfile
echo Building new Docker image...
docker build -t %DOCKER_USERNAME%/%REPO_NAME%:%IMAGE_TAG% -f Dockerfile .

:: Check if build was successful
IF %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================
    echo Build completed successfully!
    echo.
    echo To push to Docker Hub:
    echo docker push %DOCKER_USERNAME%/%REPO_NAME%:%IMAGE_TAG%
    echo =======================================
) ELSE (
    echo.
    echo Build failed! Check the errors above.
)

ENDLOCAL