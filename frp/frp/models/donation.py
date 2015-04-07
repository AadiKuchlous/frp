# -*- coding: utf-8 -*-

import inspect
from datetime import date

from . import db, BaseNameMixin, BaseMixin

__all__ = ['Donation']

class Donation(BaseMixin, db.Model):
    __tablename__ = 'donation'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    first_name = db.Column(db.String(50), nullable=False, server_default='')
    last_name = db.Column(db.String(50), nullable=True, server_default='')
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    confirmation = db.Column(db.Unicode(100), nullable=False)
    state = db.Column(db.Unicode(100), nullable=False)
    city = db.Column(db.Unicode(100), nullable=False)
    identification = db.Column(db.Unicode(100), nullable=False)

    def __add__(self,o):
        return self.amount + o.amount
    def __radd__(self,o):
        return self.amount+o