# -*- coding: utf-8 -*-
"""Provides utility functions."""


def int_factor_round(value, factor=10):
    return int(factor * round(float(value) / factor))
