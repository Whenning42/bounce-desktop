// Test that we can create a wayland backend running factorio, and that we
// can randomly move the mouse across the screen via a client while viewing the
// desktop with the SDL viewer.

#include "desktop/client.h"
#include "process/process.h"
#include "desktop/sdl_viewer.h"
#include "third_party/status/status_or.h"
#include "desktop/weston_backend.h"

const int kWidth = 800;
const int kHeight = 600;

int main(int argc, char** argv) {
  (void)argc, (void)argv;

  auto backend = std::move(
      WestonBackend::start_server(5900, kWidth, kHeight).value_or_die());

  EnvVars env = EnvVars::environ();
  for (const auto& [k, v] : backend->get_desktop_env()) {
    env.set_var(k, v);
  }

  ProcessOutConf out_conf = ProcessOutConf{
      .stdout = StreamOutConf::File("/tmp/bounce_integration_stdout.txt")
                    .value_or_die(),
      .stderr = StreamOutConf::File("/tmp/bounce_integration_stderr.txt")
                    .value_or_die(),
  };
  Process subproc = std::move(
      launch_process({"/home/william/Games/factorio/bin/x64/factorio"}, &env,
                     std::move(out_conf))
          .value_or_die());

  auto client =
      std::move(BounceDeskClient::connect(backend->port()).value_or_die());
  auto viewer = std::move(SDLViewer::open(client.get()).value_or_die());

  int x = 0;
  int y = 0;
  while (!viewer->was_closed()) {
    x = (x + 70) % kWidth;
    y = (y + 20) % kHeight;
    client->move_mouse(x, y);
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
  }

  return 0;
}
