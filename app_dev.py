import api
import config

if __name__ == '__main__':
    # run('api:api', host=config.BIND_IP, port=config.PORT, log_level='info', reload=True)
    api.app.run(config.BIND_IP, config.PORT, True)