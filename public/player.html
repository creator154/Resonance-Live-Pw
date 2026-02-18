<!DOCTYPE html>
<html>
<head>
  <title>Live Class Player</title>
  <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
</head>
<body>
  <video id="video" controls width="100%" autoplay muted></video>

  <script>
    const video = document.getElementById('video');
    const hlsUrl = 'https://d2pmv2a2n6a6po.cloudfront.net/index.m3u8';  // simple URL, cookies handle kar lenge

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => video.play());
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsUrl;
      video.addEventListener('loadedmetadata', () => video.play());
    }
  </script>
</body>
</html>
