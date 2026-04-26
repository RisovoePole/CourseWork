run:
    mvn clean package
    mvn dependency:copy-dependencies -DincludeScope=runtime -DoutputDirectory=target/libs
    docker-compose up -d
    docker attach app