#!/usr/bin/env python3

from app import create_app
from app.models import Planner

app = create_app()

with app.app_context():
    planners_without_names = Planner.query.filter(Planner.name.is_(None)).all()
    print(f"Planners without names: {len(planners_without_names)}")
    for planner in planners_without_names:
        print(f"  - {planner.phone_number}")
        
    all_planners = Planner.query.all()
    print(f"Total planners: {len(all_planners)}")
