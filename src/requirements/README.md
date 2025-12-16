# Requirements Files

This directory contains all pip-tools dependency management files.

## File Structure

- **requirements-prod.in** - Production dependencies (manually maintained)
- **requirements-prod.txt** - Compiled production requirements (auto-generated)
- **requirements-dev.in** - Development dependencies (manually maintained)
- **requirements-dev.txt** - Compiled development requirements (auto-generated)

## Usage

### Install Dependencies

```bash
# From project root
make install          # Production only
make install-dev      # Development + Production
```

### Add New Dependency

```bash
# For production
echo "package-name>=1.0.0" >> src/requirements/requirements-prod.in

# For development
echo "pytest>=7.0" >> src/requirements/requirements-dev.in

# Recompile
make compile
```

### Update Dependencies

```bash
# Update to latest versions
make upgrade

# Recompile with current versions
make compile
```

### Sync Environment

```bash
# Remove packages not in requirements-prod.txt
make sync
```

## Important Notes

1. **Never edit `.txt` files manually** - they are auto-generated
2. **Always commit both `.in` and `.txt` files** to version control
3. **Development deps reference production** via `-c requirements-prod.txt`
4. **Use semantic versioning** in `.in` files (e.g., `package>=1.0,<2.0`)
