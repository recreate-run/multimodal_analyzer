#!/usr/bin/env python3

import click

@click.command()
@click.option('--type', required=True, help="Analysis type")
@click.option('--model', required=True, help="Model name")
def test_required():
    """Test Click's standard required option behavior."""
    pass

if __name__ == '__main__':
    test_required()