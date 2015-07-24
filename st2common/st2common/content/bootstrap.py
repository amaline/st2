# Licensed to the StackStorm, Inc ('StackStorm') under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

from oslo_config import cfg

from st2common import config
from st2common.service_setup import db_setup
from st2common.service_setup import db_teardown
from st2common.logging.filters import LogLevelFilter
from st2common.transport.utils import register_exchanges


LOG = logging.getLogger('st2common.content.bootstrap')
cfg.CONF.register_cli_opt(cfg.BoolOpt('verbose', short='v', default=False))
cfg.CONF.register_cli_opt(cfg.BoolOpt('experimental', default=False))


def register_opts():
    content_opts = [
        cfg.BoolOpt('all', default=False, help='Register sensors, actions and rules.'),
        cfg.BoolOpt('sensors', default=False, help='Register sensors.'),
        cfg.BoolOpt('sensorinstances', default=False, help='Register sensor instances.'),
        cfg.BoolOpt('actions', default=False, help='Register actions.'),
        cfg.BoolOpt('rules', default=False, help='Register rules.'),
        cfg.BoolOpt('aliases', default=False, help='Register aliases.'),
        cfg.BoolOpt('policies', default=False, help='Register policies.'),
        cfg.StrOpt('pack', default=None, help='Directory to the pack to register content from.')
    ]
    try:
        cfg.CONF.register_cli_opts(content_opts, group='register')
    except:
        sys.stderr.write('Failed registering opts.\n')
register_opts()


def register_sensors():
    registered_count = 0
    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering sensors ######################')
        LOG.info('=========================================================')
        # Importing here to reduce scope of dependency. This way even if st2reactor
        # is not installed bootstrap continues.
        import st2reactor.bootstrap.sensorsregistrar as sensors_registrar
        registered_count = sensors_registrar.register_sensors(pack_dir=cfg.CONF.register.pack)
    except Exception:
        LOG.warning('Failed to register sensors.', exc_info=True)

    LOG.info('Registered %s sensors.', registered_count)


def register_sensor_instances():
    registered_count = 0
    try:
        LOG.info('=========================================================')
        LOG.info('############# Registering sensor instances ##############')
        LOG.info('=========================================================')
        # Importing here to reduce scope of dependency. This way even if st2reactor
        # is not installed bootstrap continues.
        import st2reactor.bootstrap.sensorinstancesregistrar as sensor_instances_registrar
        registered_count = sensor_instances_registrar.register_sensor_instances(
            pack_dir=cfg.CONF.register.pack)
    except Exception:
        LOG.warning('Failed to register sensors instances.', exc_info=True)

    LOG.info('Registered %s sensor instancess.', registered_count)


def register_actions():
    # Register runnertypes and actions. The order is important because actions require action
    # types to be present in the system.
    registered_count = 0

    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering actions ######################')
        LOG.info('=========================================================')
        # Importing here to reduce scope of dependency. This way even if st2action
        # is not installed bootstrap continues.
        import st2actions.bootstrap.runnersregistrar as runners_registrar
        runners_registrar.register_runner_types(experimental=cfg.CONF.experimental)
    except Exception as e:
        LOG.warning('Failed to register runner types: %s', e, exc_info=True)
        LOG.warning('Not registering stock runners .')
    else:
        try:
            # Importing here to reduce scope of dependency. This way even if st2action
            # is not installed bootstrap continues.
            import st2actions.bootstrap.actionsregistrar as actions_registrar
            registered_count = actions_registrar.register_actions(pack_dir=cfg.CONF.register.pack)
        except Exception as e:
            LOG.warning('Failed to register actions: %s', e, exc_info=True)

    LOG.info('Registered %s actions.' % (registered_count))


def register_rules():
    # Register rules.
    registered_count = 0

    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering rules ########################')
        LOG.info('=========================================================')
        # Importing here to reduce scope of dependency. This way even if st2reactor
        # is not installed bootstrap continues.
        import st2reactor.bootstrap.rulesregistrar as rules_registrar
        registered_count = rules_registrar.register_rules(pack_dir=cfg.CONF.register.pack)
    except Exception as e:
        LOG.warning('Failed to register rules: %s', e, exc_info=True)

    LOG.info('Registered %s rules.' % (registered_count))


def register_aliases():
    # Register rules.
    registered_count = 0
    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering aliases ######################')
        LOG.info('=========================================================')
        import st2common.content.aliasesregistrar as aliases_registrar
        # This count is broken. If register_aliases throws an exception it has
        # no assigned value. (FIX ME!)
        registered_count = aliases_registrar.register_aliases(pack_dir=cfg.CONF.register.pack)
    except Exception:
        LOG.warning('Failed to register aliases.', exc_info=True)

    LOG.info('Registered %s aliases.', registered_count)


def register_policies():
    # Register policy types and policies.
    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering policy types #################')
        LOG.info('=========================================================')
        import st2actions
        import st2common.content.policiesregistrar as policies_registrar
        registered_type_count = policies_registrar.register_policy_types(st2actions)
    except Exception:
        LOG.warning('Failed to register policy types.', exc_info=True)

    LOG.info('Registered %s policy types.', registered_type_count)

    try:
        LOG.info('=========================================================')
        LOG.info('############## Registering policies #####################')
        LOG.info('=========================================================')
        import st2common.content.policiesregistrar as policies_registrar
        registered_count = policies_registrar.register_policies()
    except Exception:
        LOG.warning('Failed to register policies.', exc_info=True)

    LOG.info('Registered %s policies.', registered_count)


def register_content():
    if cfg.CONF.register.all:
        register_sensors()
        register_sensor_instances()
        register_actions()
        register_rules()
        register_aliases()
        register_policies()
        return

    if cfg.CONF.register.sensors:
        register_sensors()

    if cfg.CONF.register.sensorinstances:
        register_sensor_instances()

    if cfg.CONF.register.actions:
        register_actions()

    if cfg.CONF.register.rules:
        register_rules()

    if cfg.CONF.register.aliases:
        register_aliases()

    if cfg.CONF.register.policies:
        register_policies()


def _setup(argv):
    config.parse_args()

    log_level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s %(levelname)s [-] %(message)s', level=log_level)

    if not cfg.CONF.verbose:
        # Note: We still want to print things at the following log levels: INFO, ERROR, CRITICAL
        exclude_log_levels = [logging.AUDIT, logging.DEBUG]
        handlers = logging.getLoggerClass().manager.root.handlers

        for handler in handlers:
            handler.addFilter(LogLevelFilter(log_levels=exclude_log_levels))

    db_setup()
    register_exchanges()


def _teardown():
    db_teardown()


def main(argv):
    _setup(argv)
    register_content()
    _teardown()


# This script registers actions and rules from content-packs.
if __name__ == '__main__':
    main(sys.argv[1:])
