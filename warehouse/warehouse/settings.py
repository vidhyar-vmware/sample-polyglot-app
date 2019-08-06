"""
Django settings for warehouse project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import yaml
import socket
from wavefront_sdk.common import heartbeater_service
from wavefront_opentracing_sdk.reporting import CompositeReporter, \
    WavefrontSpanReporter, ConsoleReporter
from wavefront_pyformance.tagged_registry import TaggedRegistry
from wavefront_sdk.common import ApplicationTags
from wavefront_opentracing_sdk import reporting, WavefrontTracer
from wavefront_django_sdk.tracing import DjangoTracing
from wavefront_pyformance.wavefront_reporter import WavefrontDirectReporter
from wavefront_pyformance.wavefront_reporter import WavefrontProxyReporter

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'h$upq=v3p0x8q8-mn_551ei5nxd#7(6=pzzqzzc9adezjwbbu7'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'wavefront_django_sdk.middleware.WavefrontMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'warehouse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'warehouse.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

WF_REPORTING_CONFIG = None
with open("../wfReportingConfig.yaml", "r") as stream:
    WF_REPORTING_CONFIG = yaml.load(stream)

APPLICATION_TAGS = None
with open("applicationTags.yaml", "r") as stream:
    application_tags_yaml = yaml.load(stream)
    APPLICATION_TAGS = ApplicationTags(
        application=application_tags_yaml.get('application'),
        service=application_tags_yaml.get('service'),
        cluster=application_tags_yaml.get('cluster'),
        shard=application_tags_yaml.get('shard'),
        custom_tags=application_tags_yaml.get('customTags').items()
    )

SOURCE = WF_REPORTING_CONFIG.get('source') or socket.gethostname()

WF_REPORTER = None
if WF_REPORTING_CONFIG and \
        WF_REPORTING_CONFIG.get('reportingMechanism') == 'direct':
    WF_REPORTER = WavefrontDirectReporter(
        server=WF_REPORTING_CONFIG.get('server'),
        token=WF_REPORTING_CONFIG.get('token'),
        reporting_interval=5,
        source=SOURCE
    ).report_minute_distribution()
elif WF_REPORTING_CONFIG and \
        WF_REPORTING_CONFIG.get('reportingMechanism') == 'proxy':
    WF_REPORTER = WavefrontProxyReporter(
        host=WF_REPORTING_CONFIG.get('proxyHost'),
        port=WF_REPORTING_CONFIG.get('proxyMetricsPort'),
        distribution_port=WF_REPORTING_CONFIG.get('proxyDistributionsPort'),
        tracing_port=WF_REPORTING_CONFIG.get('proxyTracingPort'),
        reporting_interval=5,
        source=SOURCE
    ).report_minute_distribution()

SPAN_REPORTER = WavefrontSpanReporter(client=WF_REPORTER.wavefront_client,
                                      source=SOURCE)

OPENTRACING_TRACING = DjangoTracing(WavefrontTracer(
    reporter=SPAN_REPORTER, application_tags=APPLICATION_TAGS))
