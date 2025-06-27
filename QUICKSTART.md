# 🚀 LV Framework Quick Start Guide

**Get your Lotka-Volterra Ecosystem Intelligence Framework running in 5 minutes!**

## One-Command Installation

### Linux/macOS
```bash
# Standard installation
./install_lv_framework.sh

# Development installation
./install_lv_framework.sh --dev

# Without Docker (manual database setup)
./install_lv_framework.sh --no-docker
```

### Windows
```cmd
# Standard installation
install_lv_framework.bat

# Development installation
install_lv_framework.bat --dev

# Without Docker
install_lv_framework.bat --no-docker
```

## Alternative: Docker Compose Setup

```bash
# Start all services (Neo4j + Qdrant)
docker-compose up -d

# With monitoring (adds Grafana + Prometheus)
docker-compose --profile monitoring up -d

# With caching (adds Redis)
docker-compose --profile cache up -d
```

## Quick Test

```bash
# Activate environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate.bat  # Windows

# Run demo
python3 demo_lv_framework.py

# Quick test
python3 -c "from mcp_neocoder.lv_ecosystem import LVEcosystem; print('✅ LV Framework imported successfully!')"
```

## First Steps

1. **Activate Environment**
   ```bash
   source .venv/bin/activate
   ```

2. **Basic Usage**
   ```python
   import asyncio
   from mcp_neocoder.lv_ecosystem import LVEcosystem
   
   async def main():
       # Your candidates
       candidates = [
           "Conservative factual analysis",
           "Creative brainstorming approach", 
           "Technical implementation strategy"
       ]
       
       # LV selection
       lv = LVEcosystem(neo4j_session, qdrant_client)
       results = await lv.select_diverse_outputs(
           candidates=candidates,
           prompt="Solve complex problem"
       )
       
       print(f"Selected {len(results['selected_outputs'])} diverse solutions!")
       print(f"Diversity score: {results['diversity_metrics']['semantic_diversity']:.3f}")
   
   asyncio.run(main())
   ```

3. **Database Access**
   - **Neo4j**: http://localhost:7474 (neo4j/lv_password_2024)
   - **Qdrant**: http://localhost:6333/dashboard

4. **Development Setup** (Optional)
   ```bash
   ./setup_dev_environment.sh
   make help  # See all development commands
   ```

## Troubleshooting

### Import Errors
```bash
# Install missing dependencies
pip install sentence-transformers neo4j qdrant-client

# Verify installation
python3 -c "import mcp_neocoder.lv_ecosystem; print('OK')"
```

### Database Connection Issues
```bash
# Check databases are running
docker ps | grep -E "(neo4j|qdrant)"

# Restart if needed
docker-compose restart
```

### Python Version Issues
```bash
# Check Python version (need 3.8+)
python3 --version

# Create fresh environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_lv.txt
```

## Next Steps

1. **Read the full documentation**: `README_LV_FRAMEWORK.md`
2. **Explore examples**: See usage examples in the README
3. **Integrate with NeoCoder**: Use LV-enhanced templates
4. **Monitor your ecosystem**: Check diversity metrics
5. **Contribute**: See development setup for contributors

## Support

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Full API reference available
- **Community**: Join discussions and share experiences

**Happy Ecosystem Building! 🧬✨**
