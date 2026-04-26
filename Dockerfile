FROM eclipse-temurin:21-jdk-alpine

WORKDIR /app
COPY target/*.jar app.jar
COPY target/libs/ libs/

ENTRYPOINT ["java", "-cp", "app.jar:libs/*", "org.app.App"]