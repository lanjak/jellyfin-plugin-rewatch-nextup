using System;
using MediaBrowser.Common.Configuration;
using MediaBrowser.Common.Plugins;
using MediaBrowser.Controller;
using MediaBrowser.Controller.Plugins;
using MediaBrowser.Model.Plugins;
using MediaBrowser.Model.Serialization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Controllers;
using Microsoft.AspNetCore.Mvc.Filters;
using Microsoft.Extensions.DependencyInjection;

namespace Jellyfin.Plugin.RewatchNextUp;

/// <summary>Turns on rewatching in Next Up for clients that do not ask for it (for example Android TV).</summary>
public class Plugin : BasePlugin<BasePluginConfiguration>
{
    public Plugin(IApplicationPaths applicationPaths, IXmlSerializer xmlSerializer)
        : base(applicationPaths, xmlSerializer)
    {
    }

    public override string Name => "Rewatch Next Up";

    public override Guid Id => Guid.Parse("a3520f75-7cfe-49e0-9b30-a3c108a5a4ce");

    public override string Description => "Shows the next episode of series you are rewatching in Next Up, on every client.";
}

public class ServiceRegistrator : IPluginServiceRegistrator
{
    public void RegisterServices(IServiceCollection serviceCollection, IServerApplicationHost applicationHost)
        => serviceCollection.Configure<MvcOptions>(options => options.Filters.Add(new RewatchNextUpFilter()));
}

public class RewatchNextUpFilter : IActionFilter
{
    public void OnActionExecuting(ActionExecutingContext context)
    {
        // An explicit value from the client (the web client's own setting) wins.
        if (context.ActionDescriptor is ControllerActionDescriptor { ControllerName: "TvShows", ActionName: "GetNextUp" }
            && !context.HttpContext.Request.Query.ContainsKey("enableRewatching"))
        {
            context.ActionArguments["enableRewatching"] = true;
        }
    }

    public void OnActionExecuted(ActionExecutedContext context)
    {
    }
}
