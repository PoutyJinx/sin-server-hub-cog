from .sinserverhub import SinServerHub


async def setup(bot):
    await bot.add_cog(SinServerHub(bot))
