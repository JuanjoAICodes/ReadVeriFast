<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ article.title }}</title>
</head>
<body>
    <main class="container">
      <article>
        <h1>{{ article.title }}</h1>
        <p>
          <small>
            Source: {{ article.source }} | Published: {{ article.publication_date|date:"Y-m-d" }}
          </small>
        </p>
        <img src="{{ article.image_url }}" alt="{{ article.title }}" style="max-width:100%; height:auto;"/>
        
        <hr>
        
        <!-- Speed Reader and Quiz Controls will go here in a future step -->
        <h3>Reading Section</h3>
        <p>Controls for the speed reader and quiz will be implemented here.</p>

        <hr>
        
        <!-- The scraped content can be displayed here for reference -->
        <h3>Full Article Content (for reference)</h3>
        <div>{{ article.content|linebreaks }}</div>
        
      </article>
    </main>
</body>
</html>
Html
3. Update URLs in verifast_app/urls.py:

Add a new path that includes the article_id to capture which article to display.

Generated python
# In verifast_app/urls.py, add this to urlpatterns:
path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
Use code with caution.
Python
4. Update the Links in verifast_app/templates/verifast_app/article_list.html:

Finally, fix the placeholder links on the article list page to point to the new detail view.

FIND:

Generated html
<a href="#">{{ article.title }}</a>
Use code with caution.
Html
REPLACE WITH:

Generated html
<a href="{% url 'verifast_app:article_detail' article.id %}">{{ article.title }}</a>
Use code with caution.
Html
Validation Steps:
Command: python manage.py check

Generated code
#### Step 2: Run the Agent to Build the Detail Page

Now, execute this new plan. In your terminal (with `venv` active), run:

```bash
python agent.py --modify create_article_detail.md
```
Approve the changes when the diff is shown.

Step 3: See the Final Result
Once the agent is finished and the server has reloaded:

Go to the "Browse Articles" page (http://127.0.0.1:8000/articles/).

Click on the title of any article in the list.

This time, it will take you to a new page like http://127.0.0.1:8000/articles/2/, where you will see the full content and title of the specific article you clicked on.