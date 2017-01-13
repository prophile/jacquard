def copy_data(from_engine, to_engine):
    with from_engine.transaction() as src:
        with to_engine.transaction() as dst:
            dst.update(src)
