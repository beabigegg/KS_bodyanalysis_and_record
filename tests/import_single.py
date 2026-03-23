"""Import a single sample with specified machine_id."""
import sys, shutil
from pathlib import Path
sys.path.insert(0, '.')
from config.settings import load_settings
from sqlalchemy import create_engine
from db.repository import RecipeRepository
from pipeline import RecipePipeline

machine_id = sys.argv[1]
sample_path = sys.argv[2]

src = Path(sample_path)
temp_dir = Path(f'temp_import/ConnX Elite/{machine_id}')
temp_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, temp_dir / src.name)

try:
    s = load_settings('config.yaml')
    engine = create_engine(s.mysql.sqlalchemy_url())
    repo = RecipeRepository(engine)
    pipeline = RecipePipeline(repository=repo)
    r = pipeline.process(str(temp_dir / src.name))
    print(f'Import ID: {r.recipe_import_id}')
    print(f'Files: {r.parsed_files}/{r.total_files} parsed, {r.skipped_files} skipped')
    print(f'Params: {r.parameter_count}, BSG: {r.bsg_count}')
    print(f'RPM limits: {r.rpm_limits_count}, RPM ref: {r.rpm_reference_count}')
finally:
    shutil.rmtree('temp_import', ignore_errors=True)
