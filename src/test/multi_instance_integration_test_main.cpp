// Test that we can create a wayland backend running factorio, and that we
// can randomly move the mouse across the screen via a client while viewing the
// desktop with the SDL viewer.

#include "desktop/client.h"
#include "desktop/sdl_viewer.h"
#include "desktop/weston_backend.h"
#include "process/process.h"
#include "src/time_aliases.h"
#include "third_party/status/status_or.h"

const int kWidth = 800;
const int kHeight = 600;

int main(int argc, char** argv) {
  (void)argc, (void)argv;
  // Note: Multiple desktops in a single process is still highly experimental
  // and has some oddities to work through, namely:
  // 1. Our libgvnc client is single threaded even when multiple instances are
  //    running. So far it looks like it behaves correctly, but this could be a
  //    performance issue.
  // 2. Our SDL viewer class isn't remotely thread safe. This integration test
  //    works around it by sleeping to prevent races at viewer start time, but
  //    it's still racing in that each viewer instance makes an unsafe call to
  //    poll the main event loop.
  // 3. Our tested app, Factorio on Weston, unexpectedly exits fullscreen mode
  //    if we try to start our second backend before connecting a client to
  //    our first backend. I'm not sure where the in the stack the issue is,
  //    but it's something to be aware of.
  //
  // For now, we're only going to support single instance per processes, but
  // it's good to have these issues identified and documented here.

  auto backend_0 = std::move(
      WestonBackend::start_server(5900, kWidth, kHeight).value_or_die());

  EnvVars env_0 = EnvVars::environ();
  for (const auto& [k, v] : backend_0->get_desktop_env()) {
    env_0.set_var(k, v);
  }

  ProcessOutConf out_conf_0 = ProcessOutConf{
      .stdout = StreamOutConf::File("/tmp/inst_0_stdout.txt").value_or_die(),
      .stderr = StreamOutConf::File("/tmp/inst_0_stderr.txt").value_or_die(),
  };
  Process subproc_0 = std::move(
      launch_process({"/home/william/Games/factorio/bin/x64/factorio"}, &env_0,
                     std::move(out_conf_0))
          .value_or_die());

  auto client_0 =
      std::move(BounceDeskClient::connect(backend_0->port()).value_or_die());

  auto backend_1 = std::move(
      WestonBackend::start_server(5900, kWidth, kHeight).value_or_die());

  EnvVars env_1 = EnvVars::environ();
  for (const auto& [k, v] : backend_1->get_desktop_env()) {
    env_1.set_var(k, v);
  }

  ProcessOutConf out_conf_1 = ProcessOutConf{
      .stdout = StreamOutConf::File("/tmp/inst_1_stdout.txt").value_or_die(),
      .stderr = StreamOutConf::File("/tmp/inst_1_stderr.txt").value_or_die(),
  };
  Process subproc_1 = std::move(
      launch_process({"/home/william/Games/factorio_copy/bin/x64/factorio"},
                     &env_1, std::move(out_conf_1))
          .value_or_die());

  auto client_1 =
      std::move(BounceDeskClient::connect(backend_1->port()).value_or_die());

  auto viewer_0 =
      std::move(SDLViewer::open(client_0.get(), "Viewer 0", /*allow_unsafe=*/true)
                    .value_or_die());
  sleep_for(200ms);
  auto viewer_1 =
      std::move(SDLViewer::open(client_1.get(), "Viewer 1", /*allow_unsafe=*/true)
                    .value_or_die());

  int x = 0;
  int y = 0;
  while (!viewer_0->was_closed() && !viewer_1->was_closed()) {
    x = (x + 70) % kWidth;
    y = (y + 20) % kHeight;
    client_0->move_mouse(x, y);
    client_1->move_mouse(kWidth - x, y);
    std::this_thread::sleep_for(std::chrono::milliseconds(250));
  }

  return 0;
}
