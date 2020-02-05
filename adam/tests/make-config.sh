#!/bin/bash
#
# This script is a helper for ci.
#
# Makes the test-config.yaml file from CI_DEV_TOKEN/CI_PROD_TOKEN
# environment variables and test-config.yaml.template file.
#

DIR=$(dirname $BASH_SOURCE)

# security: create an empty file with restrictive permissions (defends
# against someone running this on a shared machine where others may pick up
# the tokens)
echo > "$DIR/test-config.yaml"
chmod 600 "$DIR/test-config.yaml"

sed "s/\$CI_DEV_TOKEN/$CI_DEV_TOKEN/g; s/\$CI_PROD_TOKEN/$CI_PROD_TOKEN/g;" "$DIR/test-config.yaml.template" >> "$DIR/test-config.yaml"
