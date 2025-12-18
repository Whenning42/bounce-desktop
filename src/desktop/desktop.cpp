#include "desktop/desktop.h"

#include "desktop/frame.h"
#include "third_party/status/exceptions.h"

std::unique_ptr<Desktop> Desktop::create(int32_t width, int32_t height,
                                         bool visible) {
  ASSIGN_OR_RAISE(auto backend, WestonBackend::start_server(
                                    /*port_offset=*/5900, width, height));
  auto desktop = std::unique_ptr<Desktop>(new Desktop());
  desktop->backend_ = std::move(backend);
  RAISE_IF_ERROR(desktop->connect_impl(desktop->backend_->port()));

  if (visible) {
    ASSIGN_OR_RAISE(desktop->sdl_viewer_, SDLViewer::open(desktop.get()));
  }

  return desktop;
}
