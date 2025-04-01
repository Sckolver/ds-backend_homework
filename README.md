# Репозиторий к семинару "Основы backend-разработки"

## Создание контейнера

```
docker build -t ds-backend .
```

## Запуск контейнера
```
./run.sh
```

## Curl-запросы
```
curl -X GET "http://127.0.0.1:8080/externalReadPlateNumber?image_id=10022"
```

```
curl -X POST "http://127.0.0.1:8080/externalBatchReadPlateNumbers" \
  -H "Content-Type: application/json" \
  -d '{"image_ids": [10022, 9965, 99999]}'
```