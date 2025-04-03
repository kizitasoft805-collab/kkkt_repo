from django.db import models
from django.utils.timezone import now

class News(models.Model):
    """
    Model to store news articles.
    """
    title = models.CharField(max_length=255, help_text="Title of the news")
    content = models.TextField(help_text="Detailed content of the news")
    bible_reference = models.TextField(
        blank=True, null=True,
        help_text="Bible reference lines related to the news"
    )
    created_at = models.DateTimeField(default=now, help_text="Timestamp when the news was created")

    class Meta:
        ordering = ['-created_at']  # Show latest news first

    def __str__(self):
        return self.title


class NewsMedia(models.Model):
    """
    Model to store multiple media files (images, videos, and documents) for a single news post.
    """
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
    ]

    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="media", help_text="Associated news post")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, help_text="Type of media")
    file = models.FileField(upload_to="news/media/", help_text="Upload an image, video, or document")

    def __str__(self):
        return f"{self.news.title} - {self.media_type}"

class Comment(models.Model):
    """
    Model to store user comments on news articles.
    """
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="comments")
    name = models.CharField(max_length=100, blank=True, null=True, help_text="Name of the commenter (optional)")
    comment_text = models.TextField(help_text="The comment content")
    created_at = models.DateTimeField(default=now, help_text="Timestamp when the comment was made")

    class Meta:
        ordering = ['-created_at']  # Show latest comments first

    def __str__(self):
        return f"Comment by {self.name if self.name else 'Anonymous'} on {self.news.title}"
    

class Like(models.Model):
    """
    Model to store likes for news articles.
    """
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name="likes")
    session_id = models.CharField(max_length=100, help_text="Session or unique identifier for user")
    created_at = models.DateTimeField(default=now, help_text="Timestamp when the like was added")

    class Meta:
        unique_together = ("news", "session_id")  # Prevents duplicate likes per session
        ordering = ['-created_at']  # Show latest likes first

    def __str__(self):
        return f"Like on {self.news.title} by {self.session_id}"