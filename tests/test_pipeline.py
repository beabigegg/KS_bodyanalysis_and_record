"""Test script: run full pipeline on sample recipe body file."""
from pipeline import RecipePipeline
from db.repository import RecipeRepository
from config.settings import load_settings

settings = load_settings()
repo = RecipeRepository.from_settings(settings)
pipeline = RecipePipeline(repository=repo)

source = "test_data/WBK_ConneX_Elite_EAP/GWBK-0270/L_WBK_ConnX Elite@PJS6400@ECC17@WAF007957_1"
result = pipeline.process(source)

print(f"recipe_import_id: {result.recipe_import_id}")
print(f"total_files: {result.total_files}")
print(f"parsed_files: {result.parsed_files}")
print(f"skipped_files: {result.skipped_files}")
print(f"failed_files: {result.failed_files}")
print(f"parameter_count: {result.parameter_count}")
print(f"bsg_count: {result.bsg_count}")
print(f"rpm_limits_count: {result.rpm_limits_count}")
print(f"rpm_reference_count: {result.rpm_reference_count}")
