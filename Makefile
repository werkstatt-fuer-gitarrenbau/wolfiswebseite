#VIDEO_WIDTH=320
#VIDEO_HEIGHT=180
VIDEO_WIDTH=640
VIDEO_HEIGHT=360
#VIDEO_WIDTH=1280
#VIDEO_HEIGHT=720
VIDEO_ASPECT=16:9

VIDEO_SIZE=$(VIDEO_WIDTH)x$(VIDEO_HEIGHT)

NAV_IMAGES=neubau reparatur gebraucht
NAV_IMAGES_PATH=$(patsubst %,static/images/nav/%.jpg,$(NAV_IMAGES))
NAV_IMAGE_SIZE=172x300

all: images
.PHONY:all

#build after: http://diveintohtml5.info/video.html
.PHONY: videos
videos: static/videos static/videos/wfg_imagefilm_$(VIDEO_SIZE)_poster.jpg static/videos/wfg_imagefilm_$(VIDEO_SIZE).ogv static/videos/wfg_imagefilm_$(VIDEO_SIZE).mp4 static/videos/wfg_imagefilm_$(VIDEO_SIZE).webm
#videos: static/videos/wfg_imagefilm_$(VIDEO_SIZE)_poster.jpg static/videos/wfg_imagefilm_$(VIDEO_SIZE).ogv static/videos/wfg_imagefilm_$(VIDEO_SIZE).webm


static/videos:
	mkdir $@

static/videos/wfg_imagefilm_$(VIDEO_SIZE)_poster.jpg: WFG_Webseite/wfg_imagefilm_poster.png
	convert $< -resize $(VIDEO_SIZE) $@

static/videos/wfg_imagefilm_$(VIDEO_SIZE).ogv: WFG_Webseite/WFG_IMAGEFILM.mov
	ffmpeg2theora --videoquality 7 --audioquality 1 --max_size $(VIDEO_SIZE) --output=$@ $<

static/videos/wfg_imagefilm_$(VIDEO_SIZE).mp4: WFG_Webseite/WFG_IMAGEFILM.mov
	HandBrakeCLI --preset "iPhone & iPod Touch" --width $(VIDEO_WIDTH) --vb 600 --two-pass --turbo --input $< --output $@

#WFG_Webseite/WFG_IMAGEFILM.mov-$(VIDEO_SIZE)-0-log: WFG_Webseite/WFG_IMAGEFILM.mov
#	ffmpeg -pass 1 -passlogfile $<-$(VIDEO_SIZE) -threads 16  -keyint_min 0 -g 250 -skip_threshold 0 -qmin 1 -qmax 51 -i $< -vcodec libvpx -b:v 614400 -s $(VIDEO_SIZE) -aspect $(VIDEO_ASPECT) -an -y /dev/null

images: $(NAV_IMAGES_PATH)
.PHONY: images

static/videos/wfg_imagefilm_$(VIDEO_SIZE).webm: WFG_Webseite/WFG_IMAGEFILM.mov
	ffmpeg -pass 1 -passlogfile $<-$(VIDEO_SIZE) -threads 16  -keyint_min 0 -g 250 -skip_threshold 0 -qmin 1 -qmax 51 -i $< -vcodec libvpx -b:v 614400 -s $(VIDEO_SIZE) -aspect $(VIDEO_ASPECT) -an -y $@
	ffmpeg -pass 2 -passlogfile $<-$(VIDEO_SIZE) -threads 16  -keyint_min 0 -g 250 -skip_threshold 0 -qmin 1 -qmax 51 -i $< -vcodec libvpx -b:v 614400 -s $(VIDEO_SIZE) -aspect $(VIDEO_ASPECT) -acodec libvorbis -y $@

static/images/nav/%.jpg: assets/images/%.jpg Makefile
	mkdir -p `dirname $@`
	convert $< -resize $(NAV_IMAGE_SIZE)^ -extent $(NAV_IMAGE_SIZE) $@
